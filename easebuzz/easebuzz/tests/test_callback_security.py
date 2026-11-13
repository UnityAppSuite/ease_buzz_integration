"""Callback hardening: nothing reaches a payment handler unless Easebuzz signed it.

The settings document is built in memory (never inserted), so these tests leave no
Easebuzz Settings or Payment Gateway rows behind on the site they run against.
"""

from hashlib import sha512
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from easebuzz.easebuzz.doctype.easebuzz_settings.easebuzz_settings import (
	EasebuzzSettings,
	get_merchant_key,
)
from easebuzz.easebuzz.utils import callback
from frappe.tests.utils import FrappeTestCase

MERCHANT_KEY = "TESTKEYSEC1"
SALT = "TESTSALTSEC1"
REVERSE_SEQUENCE = (
	"udf10|udf9|udf8|udf7|udf6|udf5|udf4|udf3|udf2|udf1|email|firstname|productinfo|amount|txnid|key"
)
HANDLE_RESPONSE = "easebuzz.easebuzz.doctype.easebuzz_settings.easebuzz_settings.EasebuzzSettings.handle_response"


def signed(payload, salt=SALT):
	data = dict(payload)
	parts = [salt, data["status"]] + [str(data.get(field, "")) for field in REVERSE_SEQUENCE.split("|")]
	data["hash"] = sha512("|".join(parts).encode("utf-8")).hexdigest().lower()
	return data


def callback_payload(**overrides):
	data = {
		"key": MERCHANT_KEY,
		"status": "success",
		"txnid": "TXN-SEC-0001",
		"amount": "100.0",
		"productinfo": "Fee",
		"firstname": "Test",
		"email": "parent@example.com",
		"phone": "9999999999",
		"surl": "https://example.com/success",
		"furl": "https://example.com/failure",
		"udf1": "Fees",
		"udf2": "EDU-FEE-TEST-0001",
		"udf3": "Term 1",
		"udf4": "",
		"udf5": "",
	}
	data.update(overrides)
	return data


def settings_doc():
	return frappe.get_doc(
		{
			"doctype": "Easebuzz Settings",
			"easebuzz_account": "callback-security-test",
			"merchant_key": MERCHANT_KEY,
			"salt": SALT,
			"env": "test",
		}
	)


class TestEasebuzzCallbackSecurity(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Guest")
		patcher = patch.object(callback, "get_settings_for_callback", return_value=settings_doc())
		patcher.start()
		self.addCleanup(patcher.stop)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_unsigned_callback_never_reaches_a_payment_handler(self):
		with patch(HANDLE_RESPONSE) as handler, self.assertRaises(frappe.AuthenticationError):
			callback.process_callback(callback_payload(hash="0" * 128))
		handler.assert_not_called()

	def test_missing_hash_is_rejected(self):
		with patch(HANDLE_RESPONSE) as handler, self.assertRaises(frappe.AuthenticationError):
			callback.process_callback(callback_payload())
		handler.assert_not_called()

	def test_tampered_field_breaks_the_signature(self):
		data = signed(callback_payload())
		data["udf2"] = "SOMEONE-ELSES-FEE"
		with patch(HANDLE_RESPONSE) as handler, self.assertRaises(frappe.AuthenticationError):
			callback.process_callback(data)
		handler.assert_not_called()

	def test_wrong_salt_is_rejected(self):
		with patch(HANDLE_RESPONSE) as handler, self.assertRaises(frappe.AuthenticationError):
			callback.process_callback(signed(callback_payload(), salt="ATTACKER-GUESS"))
		handler.assert_not_called()

	def test_signed_callback_runs_elevated_then_restores_the_caller(self):
		seen = {}

		def record(_self, data, verified_payload=False):
			seen["user"] = frappe.session.user
			seen["verified"] = verified_payload
			seen["fee"] = data["udf2"]

		with patch(HANDLE_RESPONSE, record):
			callback.process_callback(signed(callback_payload()))

		self.assertEqual(seen, {"user": "Administrator", "verified": True, "fee": "EDU-FEE-TEST-0001"})
		self.assertEqual(frappe.session.user, "Guest")

	def test_caller_is_restored_even_when_the_handler_fails(self):
		with patch(HANDLE_RESPONSE, side_effect=frappe.ValidationError), self.assertRaises(
			frappe.ValidationError
		):
			callback.process_callback(signed(callback_payload()))
		self.assertEqual(frappe.session.user, "Guest")


class TestEasebuzzCallbackLookup(FrappeTestCase):
	def test_unknown_merchant_key_is_rejected(self):
		with self.assertRaises(frappe.AuthenticationError):
			callback.get_settings_for_callback(callback_payload(key="NOT-A-MERCHANT"))

	def test_missing_merchant_key_is_rejected(self):
		with self.assertRaises(frappe.AuthenticationError):
			callback.get_settings_for_callback(callback_payload(key=""))


class TestEasebuzzHardening(FrappeTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")

	def test_merchant_key_endpoint_is_closed_to_guests(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_merchant_key()

	def test_signed_underpayment_is_refused_before_marking_paid(self):
		fee = SimpleNamespace(
			name="EDU-FEE-TEST-0001",
			get_payment_details=lambda: {"payment_term": "Term 1", "amount": 50000},
		)
		settings = settings_doc()
		with self.assertRaises(frappe.ValidationError):
			EasebuzzSettings._validate_fee_amount(settings, fee, "Term 1", "1.00")
		EasebuzzSettings._validate_fee_amount(settings, fee, "Term 1", "50000.00")
		EasebuzzSettings._validate_fee_amount(settings, fee, "Term 1", "50450.00")
