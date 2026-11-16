"""Entry point shared by the Easebuzz webhook and the browser success redirect.

Both are reachable by anyone, so neither may trust the payload:

* The Easebuzz Settings document that verifies a callback is picked by the merchant
  ``key`` carried in the payload, not by "the last settings document". Card payments go
  through a separate surcharge merchant (``EasebuzzSettings.init_client``); verifying its
  callbacks against the other merchant's salt would reject every genuine card payment.
* The reverse hash is verified *before* anything runs with elevated rights. The payment
  handlers downstream (Fees -> Payment Entry insert/submit) need write access a Guest does
  not have, so verified callbacks are applied as Administrator; unverified ones never are.
"""

import frappe
from frappe import _


def get_settings_for_callback(data):
	key = (data or {}).get("key")
	if not key:
		frappe.throw(_("Invalid Easebuzz callback"), frappe.AuthenticationError)
	name = frappe.db.get_value("Easebuzz Settings", {"merchant_key": key}, "name")
	if not name:
		frappe.throw(_("Invalid Easebuzz callback"), frappe.AuthenticationError)
	return frappe.get_doc("Easebuzz Settings", name)


def process_callback(data):
	"""Verify one callback, then apply it. Raises on anything not signed by a configured merchant."""
	controller = get_settings_for_callback(data)
	verified = controller.validate_gateway_response(data)

	original_user = frappe.session.user
	frappe.set_user("Administrator")
	try:
		if verified.get("udf3") == "webform":
			return controller.handle_response_web_form(verified, verified_payload=True)
		return controller.handle_response(verified, verified_payload=True)
	finally:
		frappe.set_user(original_user)
