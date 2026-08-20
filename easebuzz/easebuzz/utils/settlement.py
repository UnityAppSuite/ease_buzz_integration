# Copyright (c) 2026, Hybrowlabs and contributors
# For license information, please see license.txt
"""Turn an Easebuzz Settlement Log into balanced Journal Entries.

The gateway settles fee payments to the school bank accounts and posts a
settlement payload back to us.  Step 3 of the accounting flow --
``Dr Bank / Cr Easebuzz suspense`` -- is what this module builds, so the
Easebuzz (PG suspense) account actually clears.

One Journal Entry is created **per company per settlement**.  A settlement
payload routinely spans more than one company (UESF and RESPL share a payout in
~91% of observed logs) and a Journal Entry belongs to exactly one company, so a
single JE for the whole log is not representable in ERPNext.
"""

import ast
import json

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate
from frappe.utils.synchronization import filelock

LOGGER = "easebuzz"

# Easebuzz rounds per-split charges independently of the header total; drift of
# up to ~0.15 has been observed across 400 production payloads.
DEFAULT_CHARGE_TOLERANCE = 0.50


def logger():
    return frappe.logger(LOGGER, allow_site=True, file_count=50)


class SettlementError(frappe.ValidationError):
    """Raised for anything that must stop the settlement before it posts."""


# --------------------------------------------------------------------------- #
# Payload parsing
# --------------------------------------------------------------------------- #

def parse_settlement_payload(raw):
    """Return the inner settlement dict from a stored ``Settlement Log.data``.

    ``settlement_hook`` stores ``frappe.parse_json(kwargs)``, so the field holds
    a Python ``repr`` of ``{'status': '1', 'data': '<settlement json>', 'cmd': ...}``.
    The settlement body -- ``split_payouts``, ``settled_transactions``,
    ``total_amount`` -- lives in the *inner* JSON string, not the outer wrapper.

    Accepts, in order: an already-parsed dict, a JSON string, a Python repr
    string.  Unwraps the ``{'status', 'data'}`` envelope when present.
    """
    if raw is None:
        raise SettlementError(_("Settlement Log has no payload."))

    payload = raw
    if isinstance(payload, str):
        payload = payload.strip()
        if not payload:
            raise SettlementError(_("Settlement Log has an empty payload."))
        payload = _loads(payload)

    if not isinstance(payload, dict):
        raise SettlementError(
            _("Settlement payload parsed to {0}, expected an object.").format(type(payload).__name__)
        )

    # Unwrap the {'status': '1', 'data': '<json>'} envelope.  Only treat it as an
    # envelope when the outer object does not itself carry settlement keys.
    inner = payload.get("data")
    if inner is not None and "split_payouts" not in payload and "payout_id" not in payload:
        payload = _loads(inner) if isinstance(inner, str) else inner

    if not isinstance(payload, dict):
        raise SettlementError(_("Inner settlement payload is not an object."))

    return payload


def _loads(text):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        pass
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError, TypeError) as exc:
        raise SettlementError(_("Could not parse settlement payload: {0}").format(exc))


# --------------------------------------------------------------------------- #
# Settings resolution
# --------------------------------------------------------------------------- #

def get_reconciliation_settings():
    """Resolve the Easebuzz Settings record that owns the reconciliation config.

    ``Easebuzz Settings`` is not a Single -- it is named by ``easebuzz_account``
    and a site may hold several.  ``frappe.get_last_doc`` would pick whichever
    was created last, which makes the applied rules invisible.  Resolve
    deterministically instead: prefer the single record that has reconciliation
    switched on, and refuse to guess when that is ambiguous.
    """
    names = frappe.get_all("Easebuzz Settings", pluck="name", order_by="name")
    if not names:
        return None
    if len(names) == 1:
        return frappe.get_cached_doc("Easebuzz Settings", names[0])

    enabled = frappe.get_all(
        "Easebuzz Settings",
        filters={"auto_create_journal_entry": 1},
        pluck="name",
        order_by="name",
    )
    if len(enabled) == 1:
        return frappe.get_cached_doc("Easebuzz Settings", enabled[0])
    if not enabled:
        return None

    raise SettlementError(
        _(
            "{0} Easebuzz Settings records have Auto Create Journal Entry enabled ({1}). "
            "Enable it on exactly one record so the applied charge rules are traceable."
        ).format(len(enabled), ", ".join(enabled))
    )


def load_mode_rules(settings):
    """Return ``(rules, unknown_behaviour)``.

    ``rules`` maps an Easebuzz ``transaction_type`` to whether that mode's
    charges are debited.  Returns ``(None, "Debit")`` when the rules are off,
    which means every mode's charges are debited -- the base behaviour.
    """
    if not settings or not settings.get("enable_payment_mode_rules"):
        return None, "Debit"

    rules = {}
    for row in settings.get("allowed_mode_of_payment") or []:
        key = (row.easebuzz_transaction_type or "").strip()
        if not key:
            continue
        rules[key] = bool(row.debit_charges)

    return rules, (settings.get("unknown_mode_behaviour") or "Debit")


def resolve_rule(transaction_type, rules, unknown_behaviour, unknown_modes):
    """Decide whether ``transaction_type``'s charges are debited.

    Matching is exact and case-sensitive against the raw payload value -- lower
    or strip it silently and a genuinely new Easebuzz mode looks like a
    configured one.
    """
    if rules is None:
        return True

    if transaction_type in rules:
        return rules[transaction_type]

    unknown_modes.add(transaction_type or "")
    if unknown_behaviour == "Fail":
        raise SettlementError(
            _("Unknown Easebuzz transaction_type '{0}' has no charge rule.").format(transaction_type)
        )
    return unknown_behaviour == "Debit"


# --------------------------------------------------------------------------- #
# Bank account resolution
# --------------------------------------------------------------------------- #

def resolve_bank_account(account_number):
    """Map an Easebuzz split account number onto a Bank Account and company."""
    if not account_number:
        raise SettlementError(_("A split payout carries no account_number."))

    rows = frappe.get_all(
        "Bank Account",
        filters={"bank_account_no": account_number},
        fields=["name", "account", "company", "disabled"],
    )
    if not rows:
        raise SettlementError(
            _("No Bank Account found with Easebuzz account number {0}.").format(account_number)
        )

    # A retired account and its replacement can share an account number, so match
    # on the enabled one rather than treating the pair as ambiguous.
    enabled = [row for row in rows if not row.disabled]
    if not enabled:
        raise SettlementError(
            _("Bank Account {0} for Easebuzz account number {1} is disabled.").format(
                rows[0].name, account_number
            )
        )
    if len(enabled) > 1:
        raise SettlementError(
            _("Easebuzz account number {0} matches more than one enabled Bank Account: {1}.").format(
                account_number, ", ".join(sorted(row.name for row in enabled))
            )
        )

    row = enabled[0]
    if not row.company:
        raise SettlementError(
            _("Bank Account {0} ({1}) has no company.").format(row.name, account_number)
        )
    if not row.account:
        raise SettlementError(
            _("No GL Account linked to Bank Account {0} ({1}).").format(row.name, account_number)
        )
    return row


def get_company_accounts(company):
    doc = frappe.get_cached_doc("Company", company)
    if not doc.get("default_easebuzz_account"):
        raise SettlementError(
            _("Company {0} has no Default Easebuzz Account (PG suspense) set.").format(company)
        )
    return doc


def resolve_charges_account(company_doc, settings=None):
    """Return the expense account this company's Easebuzz charges are debited to.

    The Company master wins, so a company Finance has already configured keeps
    posting where they put it.  The ``Company Charge Accounts`` table on Easebuzz
    Settings is the fallback: a company that starts settling before anyone fills
    in its Company field should not fail the whole payload.

    Returns ``None`` when neither is set -- the caller decides whether that
    matters, because a settlement whose charges are all skipped by payment-mode
    rules needs no charges account at all.
    """
    account = company_doc.get("custom_easebuzz_charges")
    if account:
        return account

    rows = settings.get("company_charge_accounts") if settings is not None else None
    for row in rows or []:
        if row.get("company") == company_doc.name and row.get("charges_account"):
            return row.get("charges_account")

    return None


# --------------------------------------------------------------------------- #
# Segregation
# --------------------------------------------------------------------------- #

def segregate(payload, rules, unknown_behaviour):
    """Group a settlement payload into per-company bank and charge buckets.

    Bank amounts come from ``split_payouts[]`` and are **never** filtered by
    payment mode -- that money physically arrived in the school's account, so
    excluding it would produce a JE that disagrees with the bank statement.

    Charges come from ``settled_transactions[].split_transactions[]`` and are
    attributed to a company through ``split_payout_id``, which is the only join
    key back to a bank split (``split_transactions[]`` carries no account
    number of its own).
    """
    splits = payload.get("split_payouts") or []
    if not splits:
        raise SettlementError(_("Settlement payload carries no split_payouts."))

    by_company = {}
    payout_to_company = {}
    unknown_modes = set()
    unallocated_charges = 0.0

    for split in splits:
        bank = resolve_bank_account(split.get("account_number"))
        company = bank.company
        get_company_accounts(company)

        bucket = by_company.setdefault(
            company,
            {
                "company": company,
                "bank_lines": [],
                "bank_total": 0.0,
                "included": 0.0,
                "skipped": 0.0,
                "skipped_modes": set(),
            },
        )
        amount = flt(split.get("payout_amount"))
        bucket["bank_lines"].append(
            {
                "account": bank.account,
                "bank_account": bank.name,
                "amount": amount,
                "account_label": split.get("account_label"),
                "split_payout_id": split.get("split_payout_id"),
                "bank_transaction_id": split.get("bank_transaction_id"),
            }
        )
        bucket["bank_total"] += amount

        split_payout_id = split.get("split_payout_id")
        if split_payout_id:
            payout_to_company[split_payout_id] = company

    for txn in payload.get("settled_transactions") or []:
        mode = txn.get("transaction_type")
        debit_charges = resolve_rule(mode, rules, unknown_behaviour, unknown_modes)

        for split_txn in txn.get("split_transactions") or []:
            charge = flt(split_txn.get("service_charge")) + flt(split_txn.get("service_tax"))
            if not charge:
                continue

            company = payout_to_company.get(split_txn.get("split_payout_id"))
            if not company:
                # No route back to a bank split, so no company to book it against.
                # Surfaced by the tolerance check below rather than silently dropped.
                unallocated_charges += charge
                continue

            bucket = by_company[company]
            if debit_charges:
                bucket["included"] += charge
            else:
                bucket["skipped"] += charge
                bucket["skipped_modes"].add(mode or _("Unknown"))

    return {
        "companies": by_company,
        "unknown_modes": unknown_modes,
        "unallocated_charges": unallocated_charges,
    }


def validate_segregation(payload, result, tolerance):
    """Check the split-level figures reconcile to the payload header."""
    companies = result["companies"]
    header_charges = flt(payload.get("service_charge_amount")) + flt(payload.get("service_tax_amount"))
    header_payout = flt(payload.get("payout_amount"))

    bank_total = sum(b["bank_total"] for b in companies.values())
    charge_total = (
        sum(b["included"] + b["skipped"] for b in companies.values())
        + result["unallocated_charges"]
    )

    problems = []
    if abs(flt(bank_total - header_payout, 2)) > tolerance:
        problems.append(
            _("Bank splits total {0} but the payload header reports payout_amount {1}.").format(
                flt(bank_total, 2), header_payout
            )
        )
    if abs(flt(charge_total - header_charges, 2)) > tolerance:
        problems.append(
            _(
                "Charges derived from split_transactions total {0} but the payload header "
                "reports {1} (service_charge_amount + service_tax_amount)."
            ).format(flt(charge_total, 2), header_charges)
        )
    if abs(flt(result["unallocated_charges"], 2)) > tolerance:
        problems.append(
            _("{0} of charges could not be attributed to a company via split_payout_id.").format(
                flt(result["unallocated_charges"], 2)
            )
        )

    if problems:
        raise SettlementError(" ".join(problems))


# --------------------------------------------------------------------------- #
# Posting
# --------------------------------------------------------------------------- #

def already_posted(payout_id, company):
    """Return an existing Journal Entry for this payout and company, if any.

    Easebuzz redelivers settlements -- payout PTOBWKJAUF arrives twice in the
    production log set -- so this is what keeps reruns from double-posting.
    Cancelled entries do not count, which lets a cancel-and-repost correction
    go through.
    """
    rows = frappe.get_all(
        "Easebuzz Settlement Reconciliation",
        filters={"payout_id": payout_id, "company": company, "journal_entry": ("is", "set")},
        pluck="journal_entry",
    )
    for name in rows:
        if frappe.db.get_value("Journal Entry", name, "docstatus") in (0, 1):
            return name
    return None


def is_first_settlement_for_company(company):
    """True until a settlement JE for this company has been submitted.

    The first JE per company is held as Draft so the mapping can be confirmed
    before anything posts to the ledger.
    """
    rows = frappe.get_all(
        "Easebuzz Settlement Reconciliation",
        filters={"company": company, "journal_entry": ("is", "set")},
        pluck="journal_entry",
    )
    for name in rows:
        if frappe.db.get_value("Journal Entry", name, "docstatus") == 1:
            return False
    return True


def build_remark(payload, log_name, bucket, currency=None):
    lines = [
        _("Easebuzz Settlement {0}").format(payload.get("payout_id")),
        _("Settlement Log: {0}").format(log_name),
        _("Company: {0}").format(bucket["company"]),
        _("Payout Date: {0}").format(getdate(payload.get("payout_date"))),
        _("Charges debited: {0}").format(fmt_money(bucket["included"], currency=currency)),
    ]
    if bucket["skipped"]:
        lines.append(
            _("Charges skipped: {0} (modes: {1})").format(
                fmt_money(bucket["skipped"], currency=currency),
                ", ".join(sorted(bucket["skipped_modes"])),
            )
        )
    return "\n".join(lines)


def build_journal_entry(payload, log_name, bucket, precision, settings=None):
    """Build one balanced Journal Entry for a single company.

    Every line is rounded to currency precision first and the suspense credit is
    then computed as the sum of the rounded debits, so the entry balances
    exactly rather than to within a rounding error.
    """
    company_doc = get_company_accounts(bucket["company"])
    charges = flt(bucket["included"], precision)
    charges_account = resolve_charges_account(company_doc, settings) if charges else None

    if charges and not charges_account:
        raise SettlementError(
            _(
                "Company {0} has no Easebuzz Charges account, but this settlement carries "
                "{1} of charges to debit. Set Easebuzz Charges on the Company, or add a row "
                "for {0} under Easebuzz Charges Accounts in Easebuzz Settings -- the settings "
                "form can create the account for you."
            ).format(bucket["company"], charges)
        )

    suspense = company_doc.default_easebuzz_account
    cost_center = company_doc.get("cost_center")
    accounts = []
    total_debit = 0.0

    for line in bucket["bank_lines"]:
        amount = flt(line["amount"], precision)
        if not amount:
            continue
        total_debit = flt(total_debit + amount, precision)
        accounts.append(
            {
                "account": line["account"],
                "bank_account": line["bank_account"],
                "cost_center": cost_center,
                "debit_in_account_currency": amount,
                "debit": amount,
                "credit_in_account_currency": 0,
                "credit": 0,
                "is_advance": "No",
                "against_account": suspense,
                # Journal Entry Account has no cheque_no field and ERPNext bank
                # reconciliation matches on the JE header's cheque_no, so the
                # per-split bank reference is carried here for traceability.
                "user_remark": " | ".join(
                    str(part)
                    for part in (
                        line.get("account_label"),
                        line.get("split_payout_id"),
                        line.get("bank_transaction_id"),
                    )
                    if part
                ),
            }
        )

    # A settlement whose charges all come from disabled modes gets no charges
    # line at all, rather than a 0.00 line.
    if charges:
        total_debit = flt(total_debit + charges, precision)
        accounts.append(
            {
                "account": charges_account,
                "cost_center": cost_center,
                "debit_in_account_currency": charges,
                "debit": charges,
                "credit_in_account_currency": 0,
                "credit": 0,
                "is_advance": "No",
                "against_account": suspense,
                "user_remark": _("Easebuzz service charge and tax"),
            }
        )

    if not accounts:
        raise SettlementError(
            _("Nothing to post for company {0} -- every line is zero.").format(bucket["company"])
        )

    accounts.append(
        {
            "account": suspense,
            "cost_center": cost_center,
            "debit_in_account_currency": 0,
            "debit": 0,
            "credit_in_account_currency": total_debit,
            "credit": total_debit,
            "is_advance": "No",
            "against_account": ", ".join(sorted({a["account"] for a in accounts})),
        }
    )

    header_txn_id = payload.get("bank_transaction_id")
    if not header_txn_id or header_txn_id == "NA":
        header_txn_id = payload.get("payout_id")

    je = frappe.new_doc("Journal Entry")
    je.update(
        {
            "is_system_generated": 1,
            "title": _("Easebuzz Settlement {0}").format(payload.get("payout_id")),
            "voucher_type": "Bank Entry",
            "naming_series": "ACC-JV-.YYYY.-",
            "company": bucket["company"],
            "posting_date": getdate(payload.get("payout_date")),
            "cheque_no": header_txn_id,
            "cheque_date": getdate(payload.get("payout_date")),
            "user_remark": build_remark(payload, log_name, bucket, company_doc.get("default_currency")),
            "mode_of_payment": "Online",
            "is_opening": "No",
        }
    )
    for account in accounts:
        je.append("accounts", account)

    return je, total_debit


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def process_settlement_log(name, force=False):
    """Parse, segregate, validate and post one Easebuzz Settlement Log.

    Safe to re-run: an already-posted (payout_id, company) pair is recorded as
    ``Already Posted`` instead of creating a second Journal Entry.
    """
    force = frappe.parse_json(force) if isinstance(force, str) else force
    doc = frappe.get_doc("Easebuzz Settlement Log", name)

    if doc.status == "Processed" and not force:
        return doc.status

    try:
        settings = get_reconciliation_settings()
        payload = parse_settlement_payload(doc.data)
        _stamp_header(doc, payload)

        if not payload.get("payout_id"):
            raise SettlementError(_("Settlement payload carries no payout_id."))
        if not doc.payout_date:
            # Without it the posting date would silently fall back to today.
            raise SettlementError(_("Settlement payload carries no payout_date."))

        start_date = settings and settings.get("reconciliation_start_date")
        if start_date and getdate(doc.payout_date) < getdate(start_date):
            return _finish(
                doc,
                "Skipped",
                _("Payout date {0} is before the reconciliation start date {1}.").format(
                    doc.payout_date, getdate(start_date)
                ),
            )

        rules, unknown_behaviour = load_mode_rules(settings)
        tolerance = flt((settings and settings.get("charge_tolerance")) or DEFAULT_CHARGE_TOLERANCE)

        result = segregate(payload, rules, unknown_behaviour)
        validate_segregation(payload, result, tolerance)

    except Exception as exc:
        logger().error(f"Easebuzz Settlement Log {name} failed preflight: {exc}")
        return _finish(doc, "Failed", str(exc))

    # Persisted before any posting so a worker that dies mid-settlement leaves a
    # visible "Processing" log rather than a silent "Pending" one.
    frappe.db.set_value(
        "Easebuzz Settlement Log", doc.name,
        {"status": "Processing", "error_message": None}, update_modified=False,
    )
    frappe.db.commit()
    doc.status = "Processing"
    doc.error_message = None
    doc.set("reconciliation", [])

    auto_submit = bool(settings and settings.get("auto_submit_journal_entry"))
    precision = frappe.get_precision("Journal Entry Account", "debit")
    if result["unknown_modes"]:
        logger().warning(
            f"Easebuzz Settlement Log {name}: transaction types with no rule: "
            f"{sorted(result['unknown_modes'])}"
        )

    # Easebuzz redelivers settlements as a *new* log, so the enqueue job_id
    # differs and `deduplicate` does not apply.  Serialise on the payout instead,
    # so the already_posted check and the insert cannot interleave.
    with filelock(f"easebuzz-settlement-{payload['payout_id']}", timeout=600):
        failures, held_for_review = _post_companies(
            doc, payload, result, auto_submit, precision, name, settings
        )

    if failures:
        return _finish(doc, "Needs Review", "\n".join(failures))
    if held_for_review:
        return _finish(
            doc,
            "Needs Review",
            _("Journal Entries are held as Draft for confirmation before auto-submit is enabled."),
        )
    return _finish(doc, "Processed", None)


def _post_companies(doc, payload, result, auto_submit, precision, name, settings=None):
    """Create one Journal Entry per company, isolating each company's failure."""
    failures = []
    held_for_review = False

    for index, company in enumerate(sorted(result["companies"])):
        bucket = result["companies"][company]
        row = {
            "company": company,
            "payout_id": payload.get("payout_id"),
            "bank_total": flt(bucket["bank_total"], precision),
            "charges_debited": flt(bucket["included"], precision),
            "charges_skipped": flt(bucket["skipped"], precision),
            "skipped_modes": ", ".join(sorted(bucket["skipped_modes"])) or None,
        }

        existing = already_posted(payload["payout_id"], company)
        if existing:
            row.update({"journal_entry": existing, "status": "Already Posted"})
            doc.append("reconciliation", row)
            continue

        # One company failing must not roll back the companies that already
        # posted, so each is wrapped in its own savepoint.
        save_point = f"easebuzz_settlement_{index}"
        frappe.db.savepoint(save_point)
        try:
            je, _total = build_journal_entry(payload, doc.name, bucket, precision, settings)
            je.insert(ignore_permissions=True)

            submit = auto_submit and not is_first_settlement_for_company(company)
            if submit:
                je.submit()
            else:
                held_for_review = True

            row.update({"journal_entry": je.name, "status": "Submitted" if submit else "Draft"})
            doc.append("reconciliation", row)
        except Exception as exc:
            frappe.db.rollback(save_point=save_point)
            logger().error(f"Easebuzz Settlement Log {name} / {company}: {exc}")
            row.update({"status": "Failed", "error": str(exc)})
            doc.append("reconciliation", row)
            failures.append(f"{company}: {exc}")

    return failures, held_for_review


def _stamp_header(doc, payload):
    doc.payout_id = payload.get("payout_id")
    if payload.get("payout_date"):
        doc.payout_date = getdate(payload.get("payout_date"))
    doc.total_amount = flt(payload.get("total_amount"))
    doc.payout_amount = flt(payload.get("payout_amount"))
    doc.charges_amount = flt(payload.get("service_charge_amount")) + flt(
        payload.get("service_tax_amount")
    )


def _finish(doc, status, message):
    """Persist the outcome.

    Reconciliation rows are never cleared here.  They are the only record of
    which (payout_id, company) pairs already have a Journal Entry, so dropping
    them on a failed re-run would let the next run post a duplicate.
    """
    doc.status = status
    doc.error_message = message
    # Tells EasebuzzSettlementLog.on_update that this save is ours, so saving the
    # outcome does not start another round of reconciliation.
    doc.flags.easebuzz_reconciling = True
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return status
