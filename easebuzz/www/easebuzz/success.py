import frappe


def get_context(context):
    try:
        if frappe.session.user == "Guest":
            frappe.local.login_manager.login_as("Administrator")
            data = frappe.form_dict
            frappe.get_last_doc("Easebuzz Settings").handle_response(data)
            frappe.local.login_manager.login_as("Guest")
        else:
            data = frappe.form_dict
            frappe.get_last_doc("Easebuzz Settings").handle_response(data)
    except Exception as e:
        frappe.logger("easebuzz").exception(e)
            