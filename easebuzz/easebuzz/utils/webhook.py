# Copyright (c) 2025, Hybrowlabs and contributors
# For license information, please see license.txt

"""
Easebuzz Webhook Logging Utilities

This module provides utilities for logging Easebuzz payment gateway webhooks.
"""

import json
from typing import Any, Dict, Optional

import frappe
from frappe.utils import get_datetime, now_datetime


def add_webhook_log(data: Dict[str, Any]) -> bool:
    """
    Create a log entry for Easebuzz webhook data.

    This function extracts relevant information from Easebuzz webhook payloads
    and creates a structured log entry in the Easebuzz Webhook Log DocType.

    Args:
        data (dict): Webhook data from Easebuzz payment gateway
            Expected fields:
            - txnid: Transaction ID
            - status: Payment status (success, failure, pending, etc.)
            - amount: Transaction amount
            - udf1: User defined field 1 (typically reference doctype)
            - udf2: User defined field 2 (typically reference docname)
            - udf3: User defined field 3 (additional context)

    Returns:
        bool: True if log created successfully, False otherwise

    Example:
        >>> webhook_data = {
        ...     "txnid": "TXN123456",
        ...     "status": "success",
        ...     "amount": "5000.00",
        ...     "udf1": "Payment Request",
        ...     "udf2": "PR-0001"
        ... }
        >>> add_webhook_log(webhook_data)
        True
    """
    try:
        # Extract transaction details
        txnid = data.get("txnid")
        status = data.get("status")
        amount = data.get("amount")

        # Extract UDF fields (user defined fields)
        # udf1 = reference doctype, udf2 = reference docname
        doctype = data.get("udf1")
        docname = data.get("udf2")

        # Format docname if needed (reverse the encoding done during payment initiation)
        if docname and isinstance(docname, str):
            docname = docname.replace("@", "(").replace("#", ")")

        # Get timestamp
        timestamp = data.get("timestamp")
        if not timestamp:
            timestamp = now_datetime()
        elif isinstance(timestamp, str):
            timestamp = get_datetime(timestamp)

        # Find student associated with this payment
        student = get_student_from_reference(doctype, docname)

        # Create Easebuzz Webhook Log document
        webhook_log = frappe.get_doc(
            {
                "doctype": "Easebuzz Webhook Log",
                "txnid": txnid,
                "status": status,
                "amount": amount,
                "timestamp": timestamp,
                "reference_doctype": doctype,
                "reference_name": docname,
                "student": student,
                "data": json.dumps(data, indent=4),
            }
        )

        # Save the webhook log (ignore permissions to allow webhook logging)
        webhook_log.insert(ignore_permissions=True)
        frappe.db.commit()

        return True

    except Exception as e:
        # Log error with full traceback
        frappe.log_error(
            title="Easebuzz Webhook Log Error",
            message=f"Failed to create webhook log: {str(e)}\n{frappe.get_traceback()}"
        )
        return False


def get_student_from_reference(doctype: Optional[str], docname: Optional[str]) -> Optional[str]:
    """
    Extract student reference from the linked document.

    Attempts to find the student associated with a payment by checking
    the reference document fields.

    Args:
        doctype (str): Reference document type
        docname (str): Reference document name

    Returns:
        str or None: Student ID if found, None otherwise

    Example:
        >>> get_student_from_reference("Payment Request", "PR-0001")
        'STU-001'
    """
    if not doctype or not docname:
        return None

    try:
        # Check if document exists
        if not frappe.db.exists(doctype, docname):
            return None

        # Special handling for Payment Request - get party field
        if doctype == "Payment Request":
            student = frappe.db.get_value(doctype, docname, "party")
            return student

        # For other doctypes, check if they have a student field
        if frappe.db.has_column(doctype, "student"):
            student = frappe.db.get_value(doctype, docname, "student")
            return student

        return None

    except Exception as e:
        # Log error but don't fail the webhook logging
        frappe.log_error(
            title="Student Extraction Error",
            message=f"Failed to extract student from {doctype} {docname}: {str(e)}"
        )
        return None
