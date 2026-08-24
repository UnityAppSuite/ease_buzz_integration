// Copyright (c) 2026, Hybrowlabs and contributors
// For license information, please see license.txt

const METHOD_PREFIX = "easebuzz.easebuzz.doctype.easebuzz_settings.easebuzz_settings.";
const KNOWN_MODES_METHOD = METHOD_PREFIX + "get_known_transaction_types";
const CHARGE_STATUS_METHOD = METHOD_PREFIX + "get_charge_account_status";
const CREATE_CHARGE_ACCOUNT_METHOD = METHOD_PREFIX + "create_charge_account";

frappe.ui.form.on("Easebuzz Settings", {
	setup(frm) {
		// An Account belongs to exactly one company, so the row's own company is
		// the only sensible scope -- and charges are always an expense ledger.
		frm.set_query("charges_account", "company_charge_accounts", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			return {
				filters: {
					company: row.company,
					is_group: 0,
					root_type: "Expense",
				},
			};
		});
	},

	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Check Charges Accounts"), () => show_charge_accounts(frm));

		if (!frm.doc.enable_payment_mode_rules) return;

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

function show_charge_accounts(frm) {
	frappe.call(CHARGE_STATUS_METHOD).then((r) => {
		const rows = r.message || [];
		if (!rows.length) {
			frappe.msgprint({
				title: __("No Settling Companies"),
				message: __(
					"No company has a Default Easebuzz Account (PG suspense) set, so no settlement can post yet."
				),
				indicator: "orange",
			});
			return;
		}

		const dialog = new frappe.ui.Dialog({
			title: __("Easebuzz Charges Accounts"),
			size: "large",
			fields: [{ fieldname: "summary", fieldtype: "HTML" }],
			primary_action_label: __("Close"),
			primary_action: () => dialog.hide(),
		});

		dialog.fields_dict.summary.$wrapper.html(render_charge_accounts(rows));
		dialog.$wrapper.on("click", "[data-create-company]", (event) => {
			const company = $(event.currentTarget).attr("data-create-company");
			create_charge_account(frm, dialog, company);
		});
		dialog.$wrapper.on("click", "[data-link-company]", (event) => {
			const $button = $(event.currentTarget);
			const company = $button.attr("data-link-company");
			const account = $button.closest("tr").find("select").val();
			if (account) apply_charge_account(frm, dialog, company, account, false);
		});
		dialog.show();
	});
}

function render_charge_accounts(rows) {
	const body = rows
		.map((row) => {
			if (row.account) {
				return `<tr>
					<td>${frappe.utils.escape_html(row.company)}</td>
					<td>${frappe.utils.escape_html(row.account)}</td>
					<td><span class="indicator-pill green">${__(row.source)}</span></td>
				</tr>`;
			}

			const options = (row.candidates || [])
				.map((name) => `<option value="${frappe.utils.escape_html(name)}">${frappe.utils.escape_html(name)}</option>`)
				.join("");
			const link = options
				? `<select class="form-control input-xs" style="display:inline-block;width:auto">${options}</select>
				   <button class="btn btn-xs btn-default" data-link-company="${frappe.utils.escape_html(row.company)}">${__("Use This")}</button>`
				: "";

			return `<tr>
				<td>${frappe.utils.escape_html(row.company)}</td>
				<td class="text-muted">${__("Not set")}</td>
				<td>
					${link}
					<button class="btn btn-xs btn-primary" data-create-company="${frappe.utils.escape_html(row.company)}">
						${__("Create {0}", [frappe.utils.escape_html(row.suggested_account_name)])}
					</button>
				</td>
			</tr>`;
		})
		.join("");

	return `<p class="text-muted small">${__(
		"Charges post to the account on the Company master first; the Company Charge Accounts table is the fallback. A company with neither is held for review when its settlement carries charges."
	)}</p>
	<table class="table table-bordered">
		<thead><tr><th>${__("Company")}</th><th>${__("Charges Account")}</th><th>${__("Source")}</th></tr></thead>
		<tbody>${body}</tbody>
	</table>`;
}

function create_charge_account(frm, dialog, company) {
	frappe
		.call({
			method: CREATE_CHARGE_ACCOUNT_METHOD,
			args: { company: company },
			freeze: true,
			freeze_message: __("Creating charges account..."),
		})
		.then((r) => {
			if (!r.message) return;
			apply_charge_account(frm, dialog, company, r.message.account, r.message.created);
		});
}

function apply_charge_account(frm, dialog, company, account, created) {
	// The row is appended and left for the user to save, so the button never
	// persists unrelated unsaved edits on the form.
	const existing = (frm.doc.company_charge_accounts || []).find((row) => row.company === company);
	if (existing) {
		frappe.model.set_value(existing.doctype, existing.name, "charges_account", account);
	} else {
		const row = frm.add_child("company_charge_accounts");
		row.company = company;
		row.charges_account = account;
	}
	frm.refresh_field("company_charge_accounts");

	frappe.show_alert({
		message: created
			? __("Created {0} and added it for {1}. Save to apply.", [account, company])
			: __("Added {0} for {1}. Save to apply.", [account, company]),
		indicator: "green",
	});
	dialog.hide();
}
