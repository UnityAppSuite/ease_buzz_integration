import frappe
import requests

@frappe.whitelist(allow_guest=True)
def webhook_handler(**kwargs):
    try:
        data = frappe.parse_json(kwargs)
        controller = frappe.get_last_doc("Easebuzz Settings")
        if data.get("udf3") == "webform":
            controller.handle_response_web_form(data)
        else:
            controller.handle_response(data)
            url = "https://fees.walnutedu.in/index.php/payment/easebuzz_webhook_callback"
            r = requests.post(url, json = data)
    except Exception as e:
        frappe.logger("easebuzz").exception(e)