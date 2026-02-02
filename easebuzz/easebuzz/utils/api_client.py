# Copyright (c) 2025, Hybrowlabs and contributors
# For license information, please see license.txt

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
    """Make HTTP request to Easebuzz API with logging."""
    request_id = frappe.generate_hash(length=10)
    start_time = time.time()

    response = None
    status_code = None
    response_text = None
    error = None
    is_success = False
    result = {}

    try:
        if method.upper() == "POST":
            response = requests.post(url, data=data, timeout=timeout)
        elif method.upper() == "GET":
            response = requests.get(url, params=data, timeout=timeout)
        else:
            response = requests.request(method, url, data=data, timeout=timeout)

        status_code = response.status_code
        response_text = response.text or None

        try:
            result = response.json()
        except (ValueError, json.JSONDecodeError):
            result = {"raw_response": response.text}

        # Easebuzz uses status=1 for success
        if status_code in (200, 201):
            if isinstance(result, dict) and result.get("status") in (1, True, "1"):
                is_success = True
            elif isinstance(result, dict) and result.get("status") in (0, False, "0"):
                error_parts = [result.get("data", ""), result.get("error_desc", "")]
                error = " - ".join(filter(None, error_parts)) or "Unknown error"
            else:
                is_success = True

        return result

    except Exception as e:
        error = f"{e!s}\n\n{frappe.get_traceback()}"
        frappe.log_error(title="Easebuzz API Error", message=error)
        return {"status": 0, "data": str(e)}

    finally:
        execution_time_ms = int((time.time() - start_time) * 1000)
        try:
            create_api_log(
                request_id=request_id,
                service=service,
                http_method=method,
                full_url=url,
                request_payload=data,
                status_code=status_code,
                response_body=response_text,
                execution_time_ms=execution_time_ms,
                is_success=is_success,
                error_details=error,
            )
        except Exception:
            pass
