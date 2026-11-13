import frappe
import requests
from easebuzz.easebuzz.utils.callback import process_callback


@frappe.whitelist(allow_guest=True, methods=["POST"])
def webhook_handler(**kwargs):
    try:
        data = frappe.parse_json(kwargs)
        result = process_callback(data)
        if data.get("udf3") == "webform":
            return result
        # Forward only after the hash has been verified, so a forged payload never
        # reaches the legacy fees system either.
        url = "https://fees.walnutedu.in/index.php/payment/easebuzz_webhook_callback"
        requests.post(url, json=data, timeout=(5, 30))
        return {"message": "ok"}
    except Exception as e:
        frappe.local.response["http_status_code"] = 400
        frappe.logger("easebuzz").exception(e)
        return {"message": "invalid callback"}
