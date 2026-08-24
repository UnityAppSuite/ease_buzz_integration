// Copyright (c) 2026, Hybrowlabs and contributors
// For license information, please see license.txt

const STATUS_COLOUR = {
	Pending: "orange",
	Processing: "blue",
	Processed: "green",
	"Needs Review": "orange",
	Failed: "red",
	Skipped: "gray",
};

frappe.ui.form.on("Easebuzz Settlement Log", {
	refresh(frm) {
		clearTimeout(frm.easebuzz_refresh_timer);
		if (frm.is_new()) return;

		// Automatic reconciliation runs just after the log's original save has
		// committed. The save response can therefore still contain Pending or
		// Processing even though the server is already working on it. Poll while
		// it is active so status, errors and reconciliation rows appear without a
		// manual browser refresh.
		const is_active =
			frm.doc.status === "Processing" ||
			(frm.doc.status === "Pending" && !frm.doc.error_message);
		if (is_active) {
			frm.easebuzz_refresh_attempts = (frm.easebuzz_refresh_attempts || 0) + 1;
			if (frm.easebuzz_refresh_attempts <= 60) {
				frm.easebuzz_refresh_timer = setTimeout(() => frm.reload_doc(), 2000);
			}
		} else {
			frm.easebuzz_refresh_attempts = 0;
		}

		if (frm.doc.status) {
			frm.page.set_indicator(__(frm.doc.status), STATUS_COLOUR[frm.doc.status] || "gray");
		}

		const processed = frm.doc.status === "Processed";
		frm.add_custom_button(processed ? __("Re-process") : __("Process"), () => {
			const run = () =>
				frm
					.call({
						method: "easebuzz.easebuzz.doctype.easebuzz_settlement_log.easebuzz_settlement_log.process_log",
						args: { docname: frm.doc.name, force: processed },
						freeze: true,
						freeze_message: __("Reconciling settlement..."),
					})
					.then(() => frm.reload_doc());

			if (!processed) return run();

			frappe.confirm(
				__(
					"This log is already Processed. Journal Entries that already exist will not be created again."
				),
				run
			);
		});
	},
});
