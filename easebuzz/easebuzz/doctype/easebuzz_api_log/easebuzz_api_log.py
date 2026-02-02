# Copyright (c) 2025, Hybrowlabs and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document


class EasebuzzAPILog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		curl_command: DF.Code | None
		error_category: DF.Literal["", "Timeout", "Connection Error", "Validation Error", "Authentication Error", "Authorization Error", "Not Found", "Rate Limit", "Server Error", "Unexpected Error"]
		error_details: DF.LongText | None
		execution_time_ms: DF.Int
		full_url: DF.SmallText | None
		http_method: DF.Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
		is_success: DF.Check
		request_headers: DF.Code | None
		request_id: DF.Data
		request_payload: DF.Code | None
		response_body: DF.Code | None
		service: DF.Data | None
		status_code: DF.Int
		timestamp: DF.Datetime
	# end: auto-generated types

	pass


def create_api_log(
	request_id: str,
	service: str,
	http_method: str,
	full_url: str,
	request_headers: dict | None = None,
	request_payload: dict | None = None,
	status_code: int | None = None,
	response_body: str | None = None,
	execution_time_ms: int | None = None,
	is_success: bool = False,
	error_category: str | None = None,
	error_details: str | None = None,
) -> str | None:
	"""Create a new Easebuzz API Log entry.

	Args:
		request_id: Unique identifier for the request
		service: Service name (e.g., "Initiate Payment", "Refund", "Transaction Status")
		http_method: HTTP method (GET, POST, DELETE, etc.)
		full_url: Complete URL of the API endpoint
		request_headers: Request headers dictionary
		request_payload: Request payload/body
		status_code: HTTP response status code
		response_body: Response body as string
		execution_time_ms: Request execution time in milliseconds
		is_success: Whether the request was successful
		error_category: Category of error if failed
		error_details: Detailed error message/traceback if failed

	Returns:
		str: Name of the created log document, or None if creation failed
	"""
	try:
		# Generate cURL command for debugging
		curl_command = _generate_curl_command(
			http_method=http_method,
			full_url=full_url,
			headers=request_headers,
			payload=request_payload
		)

		# Prepare data for logging
		log_data = {
			"doctype": "Easebuzz API Log",
			"request_id": request_id,
			"timestamp": frappe.utils.now_datetime(),
			"service": service,
			"http_method": http_method,
			"full_url": full_url,
			"request_headers": json.dumps(_sanitize_headers(request_headers), indent=2) if request_headers else None,
			"request_payload": json.dumps(_sanitize_payload(request_payload), indent=2) if request_payload else None,
			"status_code": status_code,
			"response_body": response_body if response_body else None,
			"execution_time_ms": execution_time_ms,
			"is_success": 1 if is_success else 0,
			"error_category": error_category,
			"error_details": error_details,
			"curl_command": curl_command,
		}

		# Create log document
		log_doc = frappe.get_doc(log_data)
		log_doc.insert(ignore_permissions=True)
		frappe.db.commit()

		return log_doc.name

	except Exception as e:
		# If logging fails, fall back to error log to avoid breaking the main flow
		frappe.log_error(
			f"Failed to create Easebuzz API log for request_id: {request_id}. Error: {e!s}",
			"Easebuzz API Log Creation Error"
		)
		return None


def _generate_curl_command(
	http_method: str,
	full_url: str,
	headers: dict | None = None,
	payload: dict | None = None
) -> str:
	"""Generate a cURL command equivalent to the API request.

	Args:
		http_method: HTTP method
		full_url: Complete URL
		headers: Request headers
		payload: Request payload

	Returns:
		str: cURL command string
	"""
	curl_parts = ["curl", "-X", http_method]

	# Add headers
	if headers:
		for key, value in headers.items():
			# Sanitize sensitive headers
			if key.lower() in ["authorization", "api-key", "apikey", "x-api-key", "key"]:
				value = "***REDACTED***"
			curl_parts.append(f'-H "{key}: {value}"')

	# Add payload for non-GET requests
	if payload and http_method != "GET":
		sanitized_payload = _sanitize_payload(payload)
		payload_str = json.dumps(sanitized_payload, indent=2)
		# Escape quotes for shell
		payload_str = payload_str.replace('"', '\\"')
		curl_parts.append(f'-d "{payload_str}"')

	# Add URL (always last)
	curl_parts.append(f'"{full_url}"')

	return " \\\n  ".join(curl_parts)


def _sanitize_headers(headers: dict | None) -> dict:
	"""Remove sensitive information from headers before logging.

	Args:
		headers: Headers dictionary

	Returns:
		dict: Sanitized headers
	"""
	if not headers:
		return {}

	sanitized = headers.copy()
	sensitive_keys = ["authorization", "api-key", "apikey", "x-api-key", "key", "token"]

	for key in list(sanitized.keys()):
		if key.lower() in sensitive_keys:
			sanitized[key] = "***REDACTED***"

	return sanitized


def _sanitize_payload(payload: dict | None) -> dict:
	"""Remove sensitive information from payload before logging.

	Args:
		payload: Payload dictionary

	Returns:
		dict: Sanitized payload
	"""
	if not payload:
		return {}

	sanitized = payload.copy() if isinstance(payload, dict) else payload

	if isinstance(sanitized, dict):
		# Easebuzz specific sensitive fields
		sensitive_keys = ["key", "hash", "salt", "password", "secret", "token", "api_key"]

		for key in list(sanitized.keys()):
			if key.lower() in sensitive_keys:
				sanitized[key] = "***REDACTED***"

	return sanitized
