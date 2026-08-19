// Copyright (c) 2026, Hybrowlabs and contributors
// For license information, please see license.txt

const KNOWN_MODES_METHOD =
	"easebuzz.easebuzz.doctype.easebuzz_settings.easebuzz_settings.get_known_transaction_types";

frappe.ui.form.on("Easebuzz Settings", {
	refresh(frm) {
		if (frm.is_new() || !frm.doc.enable_payment_mode_rules) return;

		// Rows are appended client-side and left for the user to save, so the
		// button never persists unrelated unsaved edits on the form.
		frm.add_custom_button(__("Add Default Payment Modes"), () => {
			frappe.call(KNOWN_MODES_METHOD).then((r) => {
				const existing = new Set(
					(frm.doc.allowed_mode_of_payment || []).map((row) =>
						(row.easebuzz_transaction_type || "").trim()
					)
				);
				const added = [];
				(r.message || []).forEach((mode) => {
					if (existing.has(mode.easebuzz_transaction_type)) return;
					const row = frm.add_child("allowed_mode_of_payment");
					row.easebuzz_transaction_type = mode.easebuzz_transaction_type;
					row.mode_of_payment = mode.mode_of_payment;
					row.debit_charges = 1;
					added.push(mode.easebuzz_transaction_type);
				});
				frm.refresh_field("allowed_mode_of_payment");
				frappe.show_alert({
					message: added.length
						? __("Added: {0}. Save to apply.", [added.join(", ")])
						: __("All known payment modes are already configured."),
					indicator: added.length ? "green" : "blue",
				});
			});
		});
	},
});

frappe.ui.form.on("Easebuzz Payment Mode Rule", {
	mode_of_payment(frm, cdt, cdn) {
		// Pre-fill the matching key, which the user can then correct to whatever
		// Easebuzz actually sends (e.g. "Netbanking", not "Net Banking").
		const row = locals[cdt][cdn];
		if (row.mode_of_payment && !row.easebuzz_transaction_type) {
			frappe.model.set_value(cdt, cdn, "easebuzz_transaction_type", row.mode_of_payment);
		}
	},
});
