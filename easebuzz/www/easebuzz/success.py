import frappe


def get_context(context):
    try:
        if frappe.session.user == "Guest":
            frappe.set_user("Administrator")
            data = frappe.form_dict
            handle_data(data)
            frappe.set_user("Guest")
        else:
            handle_data(data)
    except Exception as e:
        frappe.logger("easebuzz").exception(e)


def handle_data(data):
    controller = frappe.get_last_doc("Easebuzz Settings")
    if data.get("udf3") == "webform":
        controller.handle_response_web_form(data)
    else:
        controller.handle_response(data)
