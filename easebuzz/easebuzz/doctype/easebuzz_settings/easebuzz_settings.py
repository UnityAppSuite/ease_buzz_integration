# Copyright (c) 2023, Hybrowlabs and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document
from easebuzz.easebuzz.utils.easebuzz_payment_gateway import Easebuzz
from frappe.utils import call_hook_method
from frappe.utils.data import cint, flt
from payments.utils.utils import create_payment_gateway


# The transaction_type strings Easebuzz sends, paired with the ERPNext Mode of
# Payment they correspond to.  Matching is done on the string, not the link, so
# a missing or renamed Mode of Payment record cannot break a rule.
# Name used when the settings form creates a missing charges ledger.  ERPNext
# appends the company abbreviation, so this becomes "Easebuzz Charges - UESF".
DEFAULT_CHARGE_ACCOUNT_NAME = "Easebuzz Charges"

EASEBUZZ_TRANSACTION_TYPES = (
    ("UPI", "UPI"),
    ("Credit Card", "Credit Card"),
    ("Debit Card", "Debit Card"),
    ("Netbanking", "Netbanking"),
)


class EasebuzzSettings(Document):
    supported_currencies = ["INR"]

    def init_client(self, surcharge):
        settings = frappe.get_doc("Easebuzz Settings", {"surcharge": surcharge})
        salt = settings.get_password(fieldname="salt", raise_exception=False)
        self.client = Easebuzz(settings.merchant_key, salt, settings.env)

    def after_insert(self):
        create_payment_gateway("Easebuzz", "Easebuzz Settings", self.name)
        call_hook_method("payment_gateway_enabled", gateway="Easebuzz")

    def validate(self):
        self.validate_payment_mode_rules()
        self.validate_company_charge_accounts()

    def validate_payment_mode_rules(self):
        """Reject duplicate or blank transaction types in the charge rule table.

        Frappe does not enforce uniqueness on child rows, and two rows for the
        same mode with opposite Debit Charges settings would make the applied
        rule depend on row order.
        """
        seen = {}
        for row in self.get("allowed_mode_of_payment") or []:
            key = (row.easebuzz_transaction_type or "").strip()
            if not key:
                frappe.throw(
                    frappe._("Row #{0}: Easebuzz Transaction Type is required.").format(row.idx)
                )
            row.easebuzz_transaction_type = key
            if key in seen:
                frappe.throw(
                    frappe._(
                        "Rows #{0} and #{1} both configure the Easebuzz transaction type "
                        "'{2}'. Each mode may appear only once."
                    ).format(seen[key], row.idx, key)
                )
            seen[key] = row.idx

    def validate_company_charge_accounts(self):
        """Keep the fallback table unambiguous and postable.

        A second row for the same company would make the account that gets
        debited depend on row order, and an account belonging to another company
        would only surface as an ERPNext error deep inside a settlement job.
        """
        seen = {}
        for row in self.get("company_charge_accounts") or []:
            if row.company in seen:
                frappe.throw(
                    frappe._(
                        "Rows #{0} and #{1} both configure a charges account for {2}. "
                        "Each company may appear only once."
                    ).format(seen[row.company], row.idx, row.company)
                )
            seen[row.company] = row.idx

            account = frappe.db.get_value(
                "Account",
                row.charges_account,
                ["company", "is_group", "root_type"],
                as_dict=True,
            )
            if not account:
                frappe.throw(
                    frappe._("Row #{0}: Account {1} does not exist.").format(
                        row.idx, row.charges_account
                    )
                )
            if account.company != row.company:
                frappe.throw(
                    frappe._(
                        "Row #{0}: Account {1} belongs to {2}, not to {3}."
                    ).format(row.idx, row.charges_account, account.company, row.company)
                )
            if account.is_group:
                frappe.throw(
                    frappe._(
                        "Row #{0}: {1} is a group account. Charges must be debited to a ledger."
                    ).format(row.idx, row.charges_account)
                )
            if account.root_type != "Expense":
                frappe.throw(
                    frappe._(
                        "Row #{0}: {1} is {2}, not an Expense account."
                    ).format(row.idx, row.charges_account, account.root_type)
                )

    def validate_transaction_currency(self, currency):
        if currency not in self.supported_currencies:
            frappe.throw(
                frappe._(
                    "Please select another payment method. Easebuzz does not support transactions in currency '{0}'"
                ).format(currency)
            )

    def get_payment_url(self, **kwargs):
        try:
            doctype = kwargs.get("reference_doctype")
            docname = kwargs.get("reference_docname")
            payment_request = frappe.get_doc(doctype, docname)
            fee_doctype = payment_request.reference_doctype
            fee_docname = payment_request.reference_name
            fees = frappe.get_doc(fee_doctype, fee_docname)
            fees.reload()
            student = frappe.get_doc("Student", fees.student)
            site_url = frappe.utils.get_url()
            amounts = float(kwargs.get("amount"))

            payment_method = str(kwargs.get("payment_method"))
            show_payment_mode = get_payment_mode(payment_method)
            if show_payment_mode in ["CC", "DC"]:
                self.init_client(surcharge=1)
            else:
                self.init_client(surcharge=0)

            transaction_id = frappe.generate_hash(length=40)
            productinfo = "Payment Request for " + student.first_name
            mobile_number = student.student_mobile_number
            mobile_number = mobile_number if mobile_number else "9999999999"
            postDict = {
                "txnid": transaction_id,
                "firstname": self.process_name(student.first_name),
                "phone": mobile_number,
                "email": f"{kwargs.get('payer_email')}",
                "amount": f"{amounts}",
                "productinfo": productinfo,
                "surl": f"{site_url}/easebuzz/success?hash=" + payment_request.payment_hash,
                "furl": f"{site_url}/easebuzz/failure",
                "city": student.city,
                "zipcode": student.pincode,
                "address1": student.address_line_1,
                "address2": student.address_line_2,
                "state": student.state,
                "country": student.country,
                "show_payment_mode": show_payment_mode,
                "udf1": f"{doctype}",  # Payment Request Doctype
                "udf2": f"{docname}",  # Payment Request Docname
                "udf3": "",
                "udf4": "",
                "udf5": "",
            }

            if kwargs.get("enable_split_payment"):
                split_payments = get_split_payment(fees, payment_request.payment_term)
                postDict["split_payments"] = split_payments

            frappe.logger('ease_settle').exception(postDict)
            url = self.client.initiatePaymentAPI(postDict)
            return url
        except Exception as e:
            frappe.logger("ease_url").exception(e)
            return str(e)

    def get_payment_url_web_form(self, **kwargs):
        """
        This function is called from the web form to get the payment url
        """
        try:
            doctype = kwargs.get("reference_doctype")
            docname = kwargs.get("reference_docname")
            doc = frappe.get_doc(doctype, docname)
            docname = docname.replace("(", "@").replace(")", "#")
            student = frappe.get_doc("Student", doc.student)
            site_url = frappe.utils.get_url()
            amounts = float(kwargs.get("amount"))
            title = f"Payment for {doctype} {student.name} - {student.student_name}"

            payment_method = str(kwargs.get("payment_method"))
            show_payment_mode = get_payment_mode(payment_method)
            if show_payment_mode in ["CC", "DC"]:
                self.init_client(surcharge=1)
            else:
                self.init_client(surcharge=0)


            transaction_id = frappe.generate_hash(length=40)
            postDict = {
                "txnid": transaction_id,
                "firstname": self.process_name(student.first_name),
                "phone": student.student_mobile_number or "9999999999",
                "email": f"{kwargs.get('payer_email')}",
                "amount": f"{amounts}",
                "productinfo": title,
                "surl": f"{site_url}/easebuzz/success",
                "furl": f"{site_url}/easebuzz/failure",
                "city": student.city,
                "zipcode": student.pincode,
                "address1": student.address_line_1,
                "address2": student.address_line_2,
                "state": student.state,
                "country": student.country,
                "show_payment_mode": show_payment_mode,
                "udf1": f"{doctype}",  # Doctype
                "udf2": f"{docname}",  # Docname
                "udf3": "webform",
                "udf4": "",
                "udf5": "",
            }

            if kwargs.get("enable_split_payment") and kwargs.get("split_payments"):
                split_payments = kwargs.get("split_payments", {})
                postDict["split_payments"] = split_payments

            frappe.logger("ease_settle").exception(postDict)
            url = self.client.initiatePaymentAPI(postDict)
            return url
        except:
            frappe.log_error(
                "Error while Generating Payment Link", frappe.get_traceback()
            )


    def process_name(self,name):
        return ''.join(c for c in name if c.isalnum())

    def get_settings(self, data):
        settings = frappe._dict(
            {
                "merchant_key": self.merchant_key,
                "salt": self.get_password(fieldname="salt", raise_exception=False),
            }
        )

        if cint(data.get("notes", {}).get("use_sandbox")) or data.get("use_sandbox"):
            settings.update(
                {
                    "merchant_key": frappe.conf.sandbox_merchant_key,
                    "salt": frappe.conf.sandbox_salt,
                }
            )

        return settings

    def handle_response(self, data):
        payment_request_doctype = data.get("udf1")
        payment_request_docname = data.get("udf2")
        status = data.get("status")
        transaction_id = data.get("txnid")
        if status == "success":
            if frappe.db.exists(payment_request_doctype, payment_request_docname):
                frappe.msgprint("Payment Request exists")
                payment_request = frappe.get_doc(
                    payment_request_doctype,
                    payment_request_docname,
                    ignore_permissions=True,
                )
                frappe.db.set_value(
                    payment_request_doctype,
                    payment_request_docname,
                    "transaction_id",
                    transaction_id,
                )
                payment_request.on_payment_authorized(status="Completed")
                return {"message": "Payment Successful"}
            else:
                frappe.msgprint("Payment Request does not exist, Invalid Request")

    def handle_response_web_form(self, data):
        doctype = data.get("udf1")
        docname = data.get("udf2")
        docname = docname.replace("@", "(").replace("#", ")")
        status = data.get("status")
        transaction_id = data.get("txnid")
        if status == "success":
            if frappe.db.exists(doctype, docname):
                frappe.db.set_value(doctype, docname, "transaction_id", transaction_id)
                doc = frappe.get_doc(doctype, docname, ignore_permissions=True)
                return doc.validate_payment(data)
            else:
                frappe.log_error(f"{doctype} {docname} does not exist")

    def initiateRefund(self, data):
        amounts = float(data.get("amount"))
        refund_amount = float(data.get("refund_amount"))
        self.init_client(surcharge=0)
        transaction_id = data.get("transaction_id")
        postDict = {
            "txnid": f"{transaction_id}",
            "refund_amount": f"{refund_amount}",
            "phone": f"{data.get('phone')}",
            "email": f"{data.get('email')}",
            "amount": f"{amounts}",
        }
        response = self.client.refundAPI(postDict)
        return response


@frappe.whitelist()
def get_known_transaction_types():
    """The transaction types Easebuzz is known to report, for the settings form.

    Read-only on purpose: the rows are appended client-side so seeding cannot
    persist unrelated unsaved edits on the form.
    """
    return [
        {
            "easebuzz_transaction_type": transaction_type,
            "mode_of_payment": (
                mode_of_payment if frappe.db.exists("Mode of Payment", mode_of_payment) else None
            ),
        }
        for transaction_type, mode_of_payment in EASEBUZZ_TRANSACTION_TYPES
    ]


@frappe.whitelist()
def get_charge_account_status():
    """Report where each settling company's Easebuzz charges would be debited.

    A company settles through Easebuzz when it has a PG suspense account, so
    that is what defines "participating" -- the reconciliation never touches a
    company without one.  For each, report the account that
    ``resolve_charges_account`` would pick and, when there is none, the existing
    account that looks like the right one so the user links it instead of
    creating a second charges GL.
    """
    settings_rows = {}
    for name in frappe.get_all("Easebuzz Settings", pluck="name"):
        for row in frappe.get_all(
            "Easebuzz Company Charge Account",
            filters={"parent": name, "parenttype": "Easebuzz Settings"},
            fields=["company", "charges_account"],
        ):
            settings_rows.setdefault(row.company, row.charges_account)

    companies = frappe.get_all(
        "Company",
        filters={"default_easebuzz_account": ("is", "set")},
        fields=["name", "abbr", "custom_easebuzz_charges"],
        order_by="name",
    )

    status = []
    for company in companies:
        account = company.custom_easebuzz_charges
        source = "Company" if account else None
        if not account:
            account = settings_rows.get(company.name)
            source = "Easebuzz Settings" if account else None

        status.append(
            {
                "company": company.name,
                "account": account,
                "source": source,
                "suggested_account_name": DEFAULT_CHARGE_ACCOUNT_NAME,
                "suggested_parent": account or find_expense_parent(company.name),
                "candidates": [] if account else find_charge_account_candidates(company.name),
            }
        )
    return status


def find_charge_account_candidates(company):
    """Ledger expense accounts of this company that already look like the one."""
    return frappe.get_all(
        "Account",
        filters={
            "company": company,
            "is_group": 0,
            "root_type": "Expense",
            "account_name": ("like", "%Easebuzz%"),
        },
        pluck="name",
        order_by="name",
    )


def find_expense_parent(company):
    """The group account a new Easebuzz charges ledger should sit under."""
    for account_name in ("Indirect Expenses", "Expenses"):
        parent = frappe.db.get_value(
            "Account",
            {"company": company, "account_name": account_name, "is_group": 1},
            "name",
        )
        if parent:
            return parent

    return frappe.db.get_value(
        "Account",
        {"company": company, "root_type": "Expense", "is_group": 1, "parent_account": ("is", "not set")},
        "name",
    )


@frappe.whitelist()
def create_charge_account(company, account_name=None, parent_account=None):
    """Create the Easebuzz charges ledger for a company, or return the existing one.

    Called from the settings form when a company has no charges account, so the
    settlement does not have to be re-run against a half-configured chart of
    accounts.  Never creates a second ledger with the same name.
    """
    frappe.has_permission("Account", "create", throw=True)

    account_name = (account_name or DEFAULT_CHARGE_ACCOUNT_NAME).strip()
    existing = frappe.db.get_value(
        "Account",
        {"company": company, "account_name": account_name, "is_group": 0},
        "name",
    )
    if existing:
        return {"account": existing, "created": False}

    parent_account = parent_account or find_expense_parent(company)
    if not parent_account:
        frappe.throw(
            frappe._(
                "{0} has no expense group account to create {1} under. "
                "Create the account manually and select it here."
            ).format(company, account_name)
        )

    account = frappe.get_doc(
        {
            "doctype": "Account",
            "account_name": account_name,
            "company": company,
            "parent_account": parent_account,
            "root_type": "Expense",
            "report_type": "Profit and Loss",
            "is_group": 0,
        }
    ).insert()

    return {"account": account.name, "created": True}


@frappe.whitelist(allow_guest=True)
def get_merchant_key():
    controller = frappe.get_doc("Easebuzz Settings")
    return controller.merchant_key


def get_split_payment(fees, term=None):
    try:
        split_payments = json.loads(fees.split_payments)
        if term:
            return split_payments.get(term)
        else:
            return split_payments.get("Deposit")
    except Exception as e:
        frappe.logger("split_payment").exception(e)
        return ""


def get_payment_mode(method):
    payment_methods = {
        "net banking": "NB",
        "credit card": "CC",
        "debit card": "DC",
        "mobile wallet": "MW",
        "upi": "UPI",
    }
    return payment_methods.get(method.lower(), "")


def get_surchage():
    fee_setting = frappe.get_single("Fees Settings")
    return fee_setting.surcharge
