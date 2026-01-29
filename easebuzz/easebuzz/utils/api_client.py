# Copyright (c) 2025, Hybrowlabs and contributors
# For license information, please see license.txt

"""
Easebuzz API Client with comprehensive logging.

This module provides a centralized HTTP client for all Easebuzz API calls
with automatic logging to the Easebuzz API Log DocType.
"""

import json
import time

import frappe
import requests

from easebuzz.easebuzz.doctype.easebuzz_api_log.easebuzz_api_log import create_api_log


def make_request(
    url: str,
    data: dict,
    service: str,
    method: str = "POST",
    timeout: int = 30,
) -> dict:
    """Make HTTP request to Easebuzz API with comprehensive logging.

    Args:
        url: Full URL of the API endpoint
        data: Request payload/form data
        service: Service name for logging (e.g., "Initiate Payment", "Refund")
        method: HTTP method (default: POST)
        timeout: Request timeout in seconds (default: 30)

    Returns:
        dict: Parsed JSON response from the API
    """
    # Generate unique request ID
    request_id = frappe.generate_hash(length=10)
    start_time = time.time()

    # Initialize response tracking variables
    response = None
    status_code = None
    response_text = None
    error_category = None
    error_details = None
    is_success = False
    result = {}

    try:
        # Make the HTTP request
        if method.upper() == "POST":
            response = requests.post(url, data=data, timeout=timeout)
        elif method.upper() == "GET":
            response = requests.get(url, params=data, timeout=timeout)
        else:
            response = requests.request(method, url, data=data, timeout=timeout)

        status_code = response.status_code
        response_text = response.text if response.text else None

        # Parse JSON response
        try:
            result = response.json()
        except (ValueError, json.JSONDecodeError):
            result = {"raw_response": response.text}

        # Check for success (2xx status codes and Easebuzz status=1)
        if status_code in (200, 201):
            # Easebuzz uses status=1 for success, status=0 for failure
            if isinstance(result, dict) and result.get("status") in (1, True, "1"):
                is_success = True
            elif isinstance(result, dict) and result.get("status") in (0, False, "0"):
                # API returned an error response
                error_category = "Validation Error"
                error_details = result.get("data", result.get("error", "Unknown error"))
            else:
                # Assume success if no status field (some APIs return differently)
                is_success = True

        return result

    except requests.exceptions.Timeout:
        error_category = "Timeout"
        error_details = f"Request timed out after {timeout} seconds"
        frappe.log_error(
            f"Easebuzz API Timeout: {url}",
            "Easebuzz API Timeout"
        )
        return {"status": 0, "data": "Request timed out. Please try again."}

    except requests.exceptions.ConnectionError as e:
        error_category = "Connection Error"
        error_details = f"Failed to connect to Easebuzz API: {e!s}"
        frappe.log_error(
            f"Easebuzz API Connection Error: {e!s}",
            "Easebuzz API Connection Error"
        )
        return {"status": 0, "data": "Connection failed. Please check network and try again."}

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else None

        # Map status codes to error categories
        error_map = {
            400: "Validation Error",
            401: "Authentication Error",
            403: "Authorization Error",
            404: "Not Found",
            429: "Rate Limit",
        }

        if status_code in error_map:
            error_category = error_map[status_code]
        elif status_code and status_code >= 500:
            error_category = "Server Error"
        else:
            error_category = "Unexpected Error"

        error_details = f"HTTP {status_code}: {e!s}"
        frappe.log_error(
            f"Easebuzz API HTTP Error: {error_details}",
            "Easebuzz API HTTP Error"
        )
        return {"status": 0, "data": f"API error: {e!s}"}

    except requests.exceptions.RequestException as e:
        error_category = "Unexpected Error"
        error_details = f"Request failed: {e!s}"
        frappe.log_error(
            f"Easebuzz API Request Exception: {e!s}",
            "Easebuzz API Request Exception"
        )
        return {"status": 0, "data": f"Request failed: {e!s}"}

    except Exception as e:
        error_category = "Unexpected Error"
        error_details = f"An unexpected error occurred: {e!s}\n\n{frappe.get_traceback()}"
        frappe.log_error(
            f"Easebuzz API Unexpected Error: {e!s}",
            "Easebuzz API Unexpected Error"
        )
        return {"status": 0, "data": f"Unexpected error: {e!s}"}

    finally:
        # Always log the API call (success or failure)
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Add traceback to error details for failures
        if not is_success and error_details and "traceback" not in error_details.lower():
            error_details = f"{error_details}\n\n{frappe.get_traceback()}"

        _log_api_call(
            request_id=request_id,
            service=service,
            method=method,
            full_url=url,
            payload=data,
            status_code=status_code,
            response_body=response_text,
            execution_time_ms=execution_time_ms,
            is_success=is_success,
            error_category=error_category,
            error_details=error_details,
        )


def _log_api_call(
    request_id: str,
    service: str,
    method: str,
    full_url: str,
    payload: dict | None,
    status_code: int | None,
    response_body: str | None,
    execution_time_ms: int,
    is_success: bool,
    error_category: str | None = None,
    error_details: str | None = None,
):
    """Log API call to Easebuzz API Log doctype."""
    try:
        create_api_log(
            request_id=request_id,
            service=service,
            http_method=method,
            full_url=full_url,
            request_headers={"Content-Type": "application/x-www-form-urlencoded"},
            request_payload=payload,
            status_code=status_code,
            response_body=response_body,
            execution_time_ms=execution_time_ms,
            is_success=is_success,
            error_category=error_category,
            error_details=error_details,
        )
    except Exception as e:
        # Fall back to error log if API logging fails
        frappe.log_error(
            f"Failed to create Easebuzz API log for request {request_id}: {e!s}",
            "Easebuzz API Logging Error",
        )
