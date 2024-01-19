import frappe
import requests

@frappe.whitelist(allow_guest=True)
def webhook_handler(**kwargs):
    try:
        data = frappe.parse_json(kwargs)
        frappe.get_last_doc("Easebuzz Settings").handle_response(data)
        url = "https://fees.walnutedu.in/index.php/payment/easebuzz_webhook_callback"
        r = requests.post(url, json = data)
    except Exception as e:
        frappe.logger("easebuzz").exception(e)