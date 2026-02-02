# Copyright (c) 2025, Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase

from easebuzz.easebuzz.doctype.easebuzz_api_log.easebuzz_api_log import (
	create_api_log,
	_sanitize_headers,
	_sanitize_payload,
	_generate_curl_command,
)


class TestEasebuzzAPILog(IntegrationTestCase):
	def tearDown(self):
		# Clean up test logs
		frappe.db.delete("Easebuzz API Log", {"service": ["like", "Test%"]})
		frappe.db.commit()

	def test_create_successful_api_log(self):
		"""Test creating a successful API log entry"""
		log_name = create_api_log(
			request_id="TEST-001",
			service="Test Initiate Payment",
			http_method="POST",
			full_url="https://pay.easebuzz.in/payment/initiateLink",
			request_headers={"Content-Type": "application/json"},
			request_payload={"txnid": "TXN123", "amount": "100.00"},
			status_code=200,
			response_body='{"status": 1, "data": {"access_key": "ABC123"}}',
			execution_time_ms=250,
			is_success=True,
		)

		self.assertIsNotNone(log_name)

		log_doc = frappe.get_doc("Easebuzz API Log", log_name)
		self.assertEqual(log_doc.request_id, "TEST-001")
		self.assertEqual(log_doc.service, "Test Initiate Payment")
		self.assertEqual(log_doc.http_method, "POST")
		self.assertEqual(log_doc.status_code, 200)
		self.assertEqual(log_doc.is_success, 1)

	def test_create_error_api_log(self):
		"""Test creating an error API log entry"""
		log_name = create_api_log(
			request_id="TEST-002",
			service="Test Refund",
			http_method="POST",
			full_url="https://dashboard.easebuzz.in/api/v1/refund",
			request_headers={"Content-Type": "application/json"},
			request_payload={"txnid": "TXN456", "refund_amount": "50.00"},
			status_code=400,
			response_body='{"status": 0, "data": "Invalid transaction"}',
			execution_time_ms=150,
			is_success=False,
			error_category="Validation Error",
			error_details="Invalid transaction ID provided",
		)

		self.assertIsNotNone(log_name)

		log_doc = frappe.get_doc("Easebuzz API Log", log_name)
		self.assertEqual(log_doc.is_success, 0)
		self.assertEqual(log_doc.error_category, "Validation Error")

	def test_sanitize_headers(self):
		"""Test that sensitive headers are redacted"""
		headers = {
			"Content-Type": "application/json",
			"Authorization": "Bearer secret_token",
			"api-key": "my_api_key",
			"X-Custom-Header": "custom_value",
		}

		sanitized = _sanitize_headers(headers)

		self.assertEqual(sanitized["Content-Type"], "application/json")
		self.assertEqual(sanitized["Authorization"], "***REDACTED***")
		self.assertEqual(sanitized["api-key"], "***REDACTED***")
		self.assertEqual(sanitized["X-Custom-Header"], "custom_value")

	def test_sanitize_payload(self):
		"""Test that sensitive payload fields are redacted"""
		payload = {
			"txnid": "TXN123",
			"amount": "100.00",
			"key": "MERCHANT_KEY",
			"hash": "abc123hash",
			"salt": "my_salt",
		}

		sanitized = _sanitize_payload(payload)

		self.assertEqual(sanitized["txnid"], "TXN123")
		self.assertEqual(sanitized["amount"], "100.00")
		self.assertEqual(sanitized["key"], "***REDACTED***")
		self.assertEqual(sanitized["hash"], "***REDACTED***")
		self.assertEqual(sanitized["salt"], "***REDACTED***")

	def test_generate_curl_command(self):
		"""Test cURL command generation"""
		curl_cmd = _generate_curl_command(
			http_method="POST",
			full_url="https://pay.easebuzz.in/payment/initiateLink",
			headers={"Content-Type": "application/json", "Authorization": "Bearer token"},
			payload={"txnid": "TXN123", "key": "MERCHANT_KEY"},
		)

		self.assertIn("curl", curl_cmd)
		self.assertIn("-X POST", curl_cmd)
		self.assertIn("https://pay.easebuzz.in/payment/initiateLink", curl_cmd)
		# Sensitive data should be redacted
		self.assertIn("***REDACTED***", curl_cmd)
		self.assertNotIn("Bearer token", curl_cmd)

	def test_empty_headers(self):
		"""Test with empty/None headers"""
		sanitized = _sanitize_headers(None)
		self.assertEqual(sanitized, {})

		sanitized = _sanitize_headers({})
		self.assertEqual(sanitized, {})

	def test_empty_payload(self):
		"""Test with empty/None payload"""
		sanitized = _sanitize_payload(None)
		self.assertEqual(sanitized, {})

		sanitized = _sanitize_payload({})
		self.assertEqual(sanitized, {})

	def test_get_request_curl(self):
		"""Test cURL generation for GET requests (no payload)"""
		curl_cmd = _generate_curl_command(
			http_method="GET",
			full_url="https://dashboard.easebuzz.in/api/v1/transaction/status",
			headers={"Content-Type": "application/json"},
			payload={"txnid": "TXN123"},  # Should be ignored for GET
		)

		self.assertIn("-X GET", curl_cmd)
		self.assertNotIn("-d", curl_cmd)

	def test_timeout_error_log(self):
		"""Test logging timeout errors"""
		log_name = create_api_log(
			request_id="TEST-003",
			service="Test Transaction Status",
			http_method="GET",
			full_url="https://dashboard.easebuzz.in/api/v1/transaction/status",
			request_headers={"Content-Type": "application/json"},
			status_code=None,
			execution_time_ms=30000,
			is_success=False,
			error_category="Timeout",
			error_details="Connection timed out after 30 seconds",
		)

		self.assertIsNotNone(log_name)

		log_doc = frappe.get_doc("Easebuzz API Log", log_name)
		self.assertEqual(log_doc.error_category, "Timeout")
