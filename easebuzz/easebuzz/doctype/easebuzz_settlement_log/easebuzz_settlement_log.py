# Copyright (c) 2026, Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from easebuzz.easebuzz.utils.settlement import (
    get_reconciliation_settings,
    logger,
    parse_settlement_payload,
    process_settlement_log,
)

# Saving a log in one of these states starts (or retries) reconciliation.
# "Processed", "Processing", "Needs Review" and "Skipped" are left alone -- those
# either already posted or are waiting on a person, so re-saving must not refire.
AUTO_PROCESS_STATUSES = ("", "Pending", "Failed")


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

    def on_update(self):
        """Reconcile whenever the log is saved, insert included.

        ``on_update`` fires on both insert and subsequent saves, so this is the
        single trigger.  Re-running is safe: an already-posted
        (payout_id, company) pair is recorded as Already Posted rather than
        posted twice, which is what the original ``before_save`` hook lacked.
        """
        if self.flags.easebuzz_reconciling:
            # We are inside the save that process_settlement_log itself performs.
            return
        if (self.status or "") not in AUTO_PROCESS_STATUSES:
            return
        self.queue_reconciliation()

    @frappe.whitelist()
    def process_log(self, force=False):
        """Reconcile this log now, from the form or from the console."""
        self.check_permission("write")
        return process_settlement_log(self.name, force=force)

    def queue_reconciliation(self):
        """Hand the log to a worker, or run it after commit if there is none.

        Nothing in here may raise.  The gateway posts each settlement once, so
        an unreachable queue or a broken settings record must leave a Pending
        log to retry from -- never abort the insert and lose the payload.
        """
        try:
            settings = get_reconciliation_settings()
        except Exception as exc:
            self._note(_("Cannot resolve Easebuzz Settings: {0}").format(exc))
            return

        if not settings:
            self._note(_("No Easebuzz Settings record exists, so reconciliation is off."))
            return
        if not settings.get("auto_create_journal_entry"):
            self._note(
                _("Auto Create Journal Entry is off in Easebuzz Settings ({0}).").format(
                    settings.name
                )
            )
            return

        name = self.name
        try:
            frappe.enqueue(
                process_settlement_log,
                queue="long",
                enqueue_after_commit=True,
                job_id=f"easebuzz-settlement-{name}",
                deduplicate=True,
                name=name,
            )
            self._note(None)
        except Exception as exc:
            # No Redis or no worker.  Fall back to running after the current
            # transaction commits, which keeps it out of this save cycle.
            logger().warning(
                f"Easebuzz Settlement Log {name}: queue unavailable ({exc}); "
                "reconciling inline after commit"
            )
            self._note(None)
            frappe.db.after_commit.add(lambda: _reconcile_inline(name))

    def _note(self, message):
        """Record why reconciliation did or did not start, without rerunning hooks."""
        if (self.error_message or None) == (message or None):
            return
        self.error_message = message
        self.db_set("error_message", message, update_modified=False)


def _reconcile_inline(name):
    """Run reconciliation outside the save cycle; never let it escape."""
    try:
        process_settlement_log(name)
    except Exception:
        logger().error(
            f"Easebuzz Settlement Log {name}: inline reconciliation failed\n"
            f"{frappe.get_traceback()}"
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
