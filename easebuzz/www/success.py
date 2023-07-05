import frappe


def get_context(context):
    data = frappe.form_dict
    frappe.get_doc("EaseBuzz Settings").handle_response(data)
