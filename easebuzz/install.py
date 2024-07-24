import frappe
from easebuzz.overrides.company import create_account_head, ACCOUNT_HEADS


def after_install():
    companies = frappe.get_all("Company", pluck="name")
    for company in companies:
        for account_head in ACCOUNT_HEADS:
            create_account_head(
                account_head["account_name"],
                account_head["parent_account_name"],
                company,
            )
