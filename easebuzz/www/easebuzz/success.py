import frappe
from easebuzz.easebuzz.utils.callback import process_callback


def get_context(context):
    try:
        process_callback(frappe.form_dict)
    except Exception as e:
        frappe.local.response["http_status_code"] = 400
        frappe.logger("easebuzz").exception(e)
