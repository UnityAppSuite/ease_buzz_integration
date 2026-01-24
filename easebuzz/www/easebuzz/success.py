import frappe


def get_context(context):
    redirect_url = "/"
    try:
        data = frappe.form_dict
        if frappe.session.user == "Guest":
            frappe.set_user("Administrator")
            redirect_url = handle_data(data)
            frappe.set_user("Guest")
        else:
            redirect_url = handle_data(data)
    except Exception as e:
        frappe.logger("easebuzz").exception(e)
    finally:
        # Redirect directly to payment page
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = redirect_url


def handle_data(data):
    controller = frappe.get_last_doc("Easebuzz Settings")
    if data.get("udf3") == "webform":
        controller.handle_response_web_form(data)
        return data.get("redirect_to") or "/"

    # Process the payment
    controller.handle_response(data)

    # Build redirect URL to payment page
    doctype = data.get("udf1")
    fee_hash = data.get("udf5")

    if doctype == "Student Applicant":
        # For applicant, udf2 contains the applicant_id (may be encoded)
        applicant_id = controller.format_data(data.get("udf2"), reverse=True)
        return f"/payment?applicant_id={applicant_id}"
    elif fee_hash:
        return f"/payment?fee_id={fee_hash}"
    elif doctype == "Fees":
        # Try to get fee_hash from Fees document
        docname = controller.format_data(data.get("udf2"), reverse=True)
        fee_hash = frappe.db.get_value("Fees", docname, "fee_hash")
        if fee_hash:
            return f"/payment?fee_id={fee_hash}"

    return "/"
