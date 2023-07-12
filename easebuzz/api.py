import frappe

@frappe.whitelist(allow_guest=True)
def webhook_handler(**kwargs):
    try:
        data = frappe.parse_json(kwargs)
        frappe.get_doc("EaseBuzz Settings").handle_response(data)
    except Exception as e:
        frappe.log_error(e)