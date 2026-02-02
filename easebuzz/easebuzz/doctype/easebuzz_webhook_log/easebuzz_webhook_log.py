# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EasebuzzWebhookLog(Document):
	"""
	Log for Easebuzz payment gateway webhook events.

	This DocType stores all webhook notifications received from Easebuzz
	for payment transactions, providing an audit trail and debugging capability.
	"""

	pass
