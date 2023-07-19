import frappe


def get_context(context):
    frappe.local.login_manager.login_as("Administrator")
    data = frappe.form_dict
    frappe.get_doc("EaseBuzz Settings").handle_response(data)
    frappe.local.login_manager.login_as("Guest")