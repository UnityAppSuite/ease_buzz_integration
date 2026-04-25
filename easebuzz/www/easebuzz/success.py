import frappe


def get_context(context):
    try:
        handle_data(frappe.form_dict)
    except Exception as e:
        frappe.local.response["http_status_code"] = 400
        frappe.logger("easebuzz").exception(e)


def handle_data(data):
    controller = frappe.get_last_doc("Easebuzz Settings")
    if data.get("udf3") == "webform":
        controller.handle_response_web_form(data)
    else:
        controller.handle_response(data)
