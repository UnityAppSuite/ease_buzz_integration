import frappe
import requests

from easebuzz.easebuzz.utils.webhook import add_webhook_log


@frappe.whitelist(allow_guest=True, methods=["POST"])
def webhook_handler(**kwargs):
    try:
        data = frappe.parse_json(kwargs)

        # Log webhook data before processing
        add_webhook_log(data)

        controller = frappe.get_last_doc("Easebuzz Settings")
        if data.get("udf3") == "webform":
            controller.handle_response_web_form(data)
        else:
            controller.handle_response(data)
            url = "https://fees.walnutedu.in/index.php/payment/easebuzz_webhook_callback"
            r = requests.post(url, json = data)
    except Exception as e:
        frappe.logger("easebuzz").exception(e)