# Copyright (c) 2026, Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from easebuzz.easebuzz.utils.settlement import (
    get_reconciliation_settings,
    parse_settlement_payload,
    process_settlement_log,
)


class EasebuzzSettlementLog(Document):
    def before_insert(self):
        """Stamp the payout header so the list view is usable even if posting fails."""
        if self.payout_id:
            return
        try:
            payload = parse_settlement_payload(self.data)
        except Exception:
            return
        self.payout_id = payload.get("payout_id")
        if payload.get("payout_date"):
            self.payout_date = frappe.utils.getdate(payload.get("payout_date"))

    @frappe.whitelist()
    def process_log(self, force=False):
        """Reconcile this log now, from the form or from the console.

        Kept as a document method because the reconciliation branch exposes it
        that way; the real work lives in ``utils.settlement``.
        """
        self.check_permission("write")
        return process_settlement_log(self.name, force=force)

    def after_insert(self):
        """Queue reconciliation.

        Enqueued rather than run inline: a settlement carries up to 17 bank
        splits and ~90 transactions, which is too much for the webhook request.
        Runs on insert only -- on ``before_save`` it would re-post on every
        subsequent save of the log.
        """
        try:
            settings = get_reconciliation_settings()
        except Exception as exc:
            # The gateway posts this payload once.  An ambiguous or broken
            # settings record must leave a Pending log to retry from, never
            # abort the insert and lose the settlement.
            frappe.logger("easebuzz", allow_site=True).error(
                f"Easebuzz Settlement Log {self.name}: cannot resolve settings: {exc}"
            )
            return

        if not settings or not settings.get("auto_create_journal_entry"):
            return

        frappe.enqueue(
            process_settlement_log,
            queue="long",
            enqueue_after_commit=True,
            job_id=f"easebuzz-settlement-{self.name}",
            deduplicate=True,
            name=self.name,
        )


@frappe.whitelist()
def process_log(docname=None, doc=None, method=None, force=False):
    """Process a settlement log on demand, from the form or from the console."""
    name = docname
    if not name and doc is not None:
        name = doc if isinstance(doc, str) else doc.name
    if not name:
        frappe.throw(_("No Easebuzz Settlement Log specified."))

    frappe.has_permission("Easebuzz Settlement Log", "write", doc=name, throw=True)
    return process_settlement_log(name, force=force)
