import frappe
import requests


@frappe.whitelist(allow_guest=True)
def webhook_handler(**kwargs):
    try:
        data = frappe.parse_json(kwargs)
        controller = frappe.get_last_doc("Easebuzz Settings")
        if data.get("udf3") == "webform":
            return controller.handle_response_web_form(data)
        controller.handle_response(data)
        url = "https://fees.walnutedu.in/index.php/payment/easebuzz_webhook_callback"
        requests.post(url, json=data, timeout=(5, 30))
        return {"message": "ok"}
    except Exception as e:
        frappe.local.response["http_status_code"] = 400
        frappe.logger("easebuzz").exception(e)
        return {"message": "invalid callback"}
