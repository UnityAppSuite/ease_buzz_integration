# See license.txt

from hashlib import sha512
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from easebuzz.easebuzz.utils.payment_safety import all_salts, signature_valid, switch

SALT = "test-salt-not-real"
OTHER_SALT = "other-test-salt-not-real"
SAFETY_MODULE = "easebuzz.easebuzz.utils.payment_safety"
SETTINGS_MODULE = "easebuzz.easebuzz.doctype.easebuzz_settings.easebuzz_settings"


def make_hash(data, salt, additional_charges=None):
	"""Independent build of Easebuzz's documented reverse hash sequence."""
	fields = ["udf10", "udf9", "udf8", "udf7", "udf6", "udf5", "udf4", "udf3", "udf2", "udf1"]
	fields += ["email", "firstname", "productinfo", "amount", "txnid", "key"]
	text = "|".join([salt, data["status"]] + [str(data.get(f, "")) for f in fields])
	if additional_charges is not None:
		text = f"{additional_charges}|{text}"
	return sha512(text.encode("utf-8")).hexdigest()


def callback(salt=SALT, **extra):
	data = {
		"key": "TESTKEY123",
		"txnid": "TXN-0001",
		"amount": "1500.0",
		"status": "success",
		"email": "parent@example.com",
		"firstname": "Test Parent",
		"productinfo": "Fees",
		"udf1": "Fees",
		"udf2": "FEE-0001",
		"udf3": "Term 1",
	}
	data.update(extra)
	data["hash"] = make_hash(data, salt, data.get("additional_charges"))
	return data


class FakeFees:
	"""Stands in for a Fees document; records whether the payment was applied."""

	def __init__(self, calls, error=None):
		self.calls = calls
		self.error = error

	def on_payment_authorized(self, **kwargs):
		self.calls.append(("on_payment_authorized", kwargs))
		if self.error:
			raise self.error


class FakeLoginManager:
	"""LoginManager needs an HTTP request, which a test run does not have."""

	def __init__(self, events):
		self.events = events

	def login_as(self, user):
		self.events.append(("login", user))

	def logout(self):
		self.events.append(("logout",))


class TestSignatureValid(FrappeTestCase):
	def test_genuine_hash_accepted(self):
		self.assertTrue(signature_valid(callback(), [SALT]))

	def test_hash_case_insensitive(self):
		data = callback()
		data["hash"] = data["hash"].upper()
		self.assertTrue(signature_valid(data, [SALT]))

	def test_tampered_fields_rejected(self):
		for field, value in (
			("amount", "1.0"),
			("status", "failure"),
			("udf2", "FEE-9999"),
			("txnid", "TXN-EVIL"),
		):
			data = callback()
			data[field] = value
			self.assertFalse(signature_valid(data, [SALT]), field)

	def test_missing_or_empty_hash_rejected(self):
		data = callback()
		data.pop("hash")
		self.assertFalse(signature_valid(data, [SALT]))
		data["hash"] = ""
		self.assertFalse(signature_valid(data, [SALT]))
		data["hash"] = None
		self.assertFalse(signature_valid(data, [SALT]))

	def test_no_salts_rejected(self):
		self.assertFalse(signature_valid(callback(), []))

	def test_wrong_salt_rejected(self):
		self.assertFalse(signature_valid(callback(salt=OTHER_SALT), [SALT]))

	def test_any_salt_accepted(self):
		data = callback(salt=OTHER_SALT)
		self.assertTrue(signature_valid(data, [SALT, OTHER_SALT]))

	def test_additional_charges_prefix(self):
		data = callback(additional_charges="12.5")
		self.assertTrue(signature_valid(data, [SALT]))

		# hash computed without the prefix must not pass once additional_charges is present
		wrong = callback()
		wrong["additional_charges"] = "12.5"
		self.assertFalse(signature_valid(wrong, [SALT]))

		# hash computed with a different prefix value is rejected
		bad_prefix = callback(additional_charges="12.5")
		bad_prefix["additional_charges"] = "99.0"
		self.assertFalse(signature_valid(bad_prefix, [SALT]))

	def test_data_not_mutated(self):
		data = callback(additional_charges="12.5")
		before = dict(data)
		signature_valid(data, [SALT])
		self.assertEqual(data, before)


class TestSalts(FrappeTestCase):
	def test_all_salts_covers_every_settings_doc(self):
		for account, key, salt, surcharge in (
			("Safety Test A", "SAFETYKEYA", SALT, 0),
			("Safety Test B", "SAFETYKEYB", OTHER_SALT, 1),
		):
			frappe.get_doc(
				{
					"doctype": "Easebuzz Settings",
					"easebuzz_account": account,
					"merchant_key": key,
					"salt": salt,
					"env": "test",
					"surcharge": surcharge,
				}
			).insert(ignore_permissions=True)

		salts = all_salts()
		self.assertIn(SALT, salts)
		self.assertIn(OTHER_SALT, salts)
		self.assertTrue(signature_valid(callback(salt=OTHER_SALT), salts))
		self.assertFalse(signature_valid(callback(salt="unknown-salt"), salts))


class TestSwitch(FrappeTestCase):
	def test_missing_doctype_or_field_is_off(self):
		self.assertFalse(switch("field_that_does_not_exist"))
		with patch(f"{SAFETY_MODULE}.SETTINGS_DOCTYPE", "No Such Doctype"):
			self.assertFalse(switch("bis_verify_gateway_signature"))

	def test_reads_check_value(self):
		with patch.object(frappe.db, "get_single_value", return_value=1):
			self.assertTrue(switch("bis_verify_gateway_signature"))
		with patch.object(frappe.db, "get_single_value", return_value=0):
			self.assertFalse(switch("bis_verify_gateway_signature"))
		with patch.object(frappe.db, "get_single_value", return_value=None):
			self.assertFalse(switch("bis_verify_gateway_signature"))


class TestHandleResponse(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.events = []
		self.settings = frappe.new_doc("Easebuzz Settings")

	def tearDown(self):
		frappe.set_user("Administrator")

	def run_handle_response(self, data, switches, error=None):
		"""Run handle_response with the given switch values; return (result, events)."""
		events = self.events
		fees = FakeFees(events, error=error)
		real_get_doc = frappe.get_doc

		def get_doc(*args, **kwargs):
			if args and args[0] == "Fees":
				return fees
			return real_get_doc(*args, **kwargs)

		def log_error(*args, **kwargs):
			events.append(("log_error", args, kwargs))

		with (
			patch(f"{SETTINGS_MODULE}.LoginManager", side_effect=lambda: FakeLoginManager(events)),
			patch(f"{SETTINGS_MODULE}.switch", side_effect=lambda name: switches.get(name, False)),
			patch(f"{SETTINGS_MODULE}.all_salts", return_value=[SALT]),
			patch.object(frappe.db, "exists", return_value=True),
			patch.object(frappe, "get_doc", side_effect=get_doc),
			patch.object(frappe, "log_error", side_effect=log_error),
			patch.object(frappe.db, "rollback", side_effect=lambda *a, **k: events.append(("rollback",))),
		):
			result = self.settings.handle_response(data)
		return result, events

	def names(self):
		"""Event names, ignoring the login/logout bookkeeping."""
		return [event[0] for event in self.events if event[0] not in ("login", "logout")]

	def test_switches_off_reaches_payment_even_with_bad_hash(self):
		data = callback()
		data["hash"] = "0" * 128
		result, _ = self.run_handle_response(data, {})
		self.assertEqual(result, {"message": "Payment Successful"})
		self.assertEqual(self.names(), ["on_payment_authorized"])

	def test_signature_switch_accepts_genuine_hash(self):
		result, _ = self.run_handle_response(callback(), {"bis_verify_gateway_signature": True})
		self.assertEqual(result, {"message": "Payment Successful"})
		self.assertEqual(self.names(), ["on_payment_authorized"])

	def test_signature_switch_rejects_bad_hash_without_leaking(self):
		data = callback()
		data["amount"] = "1.0"  # tampered after hashing
		result, _ = self.run_handle_response(data, {"bis_verify_gateway_signature": True})

		self.assertEqual(result, {"message": "Invalid signature"})
		self.assertEqual(self.names(), ["log_error"])
		self.assertNotIn(("login", "Administrator"), self.events)  # rejected before login
		_, args, kwargs = next(e for e in self.events if e[0] == "log_error")
		logged = repr((args, kwargs))
		self.assertIn("Easebuzz callback rejected: hash mismatch", logged)
		self.assertIn("TXN-0001", logged)
		self.assertNotIn(data["hash"], logged)
		self.assertNotIn(SALT, logged)

	def test_signature_switch_rejects_missing_hash(self):
		data = callback()
		data.pop("hash")
		result, _ = self.run_handle_response(data, {"bis_verify_gateway_signature": True})
		self.assertEqual(result, {"message": "Invalid signature"})
		self.assertEqual(self.names(), ["log_error"])

	def test_rollback_switch_on_rolls_back_before_logging(self):
		result, _ = self.run_handle_response(
			callback(), {"bis_rollback_failed_payments": True}, error=RuntimeError("boom")
		)
		self.assertEqual(result, {"message": "Payment processing failed"})
		self.assertEqual(self.names(), ["on_payment_authorized", "rollback", "log_error"])

	def test_rollback_switch_off_does_not_roll_back(self):
		result, _ = self.run_handle_response(callback(), {}, error=RuntimeError("boom"))
		self.assertEqual(result, {"message": "Payment processing failed"})
		self.assertEqual(self.names(), ["on_payment_authorized", "log_error"])
