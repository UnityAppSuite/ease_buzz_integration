import frappe
from easebuzz.overrides.company import delete_account_head, ACCOUNT_HEADS


def after_uninstall():
    # Fetch all company names at once
    companies = frappe.get_all("Company", pluck="name")
    for company in companies:
        for account_head in ACCOUNT_HEADS:
            delete_account_head(account_head["account_name"], company)
