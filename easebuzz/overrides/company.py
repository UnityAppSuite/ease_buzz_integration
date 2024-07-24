import frappe

ACCOUNT_HEADS = [
    {
        "account_name": "Easebuzz",
        "parent_account_name": "Bank Accounts",
    }
]

def on_update(doc, method=None):
    """
    This method creates the account heads for the company.
    """
    for account_head in ACCOUNT_HEADS:
        create_account_head(
            account_head["account_name"],
            account_head["parent_account_name"],
            doc.name,
        )


def create_account_head(account_name, parent_account_name, company, account_type=None):
    """
    This method creates accounts for the company.
    """
    parent = frappe.get_value(
        "Account",
        {"account_name": parent_account_name, "company": company},
        "name",
    )

    if not parent:
        return

    if frappe.db.exists("Account", {"account_name": account_name, "company": company}):
        return

    account = frappe.get_doc(
        {
            "doctype": "Account",
            "account_name": account_name,
            "account_type": account_type,
            "company": company,
            "parent_account": parent,
        }
    )
    account.insert(ignore_permissions=True)


def delete_account_head(account_name, company):
    """
    This method deletes the specified account for the company if it exists.
    """
    # Directly attempt to delete the account without checking if it exists
    account_key = {"account_name": account_name, "company": company}
    existing_account = frappe.get_value("Account", account_key, "name")
    if existing_account:
        frappe.delete_doc("Account", existing_account)
        frappe.db.commit()
