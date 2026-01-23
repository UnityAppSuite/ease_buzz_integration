import frappe


def get_context(context):
    """
    Handle redirect from Easebuzz after payment failure.
    Redirects directly to payment page.
    """
    redirect_url = "/"
    try:
        data = frappe.form_dict

        # Extract identifiers from Easebuzz data
        doctype = data.get("udf1")
        fee_hash = data.get("udf5")

        if doctype == "Student Applicant":
            # Get applicant_id (may be encoded with @ for ( and # for ))
            controller = frappe.get_last_doc("Easebuzz Settings")
            applicant_id = controller.format_data(data.get("udf2"), reverse=True)
            redirect_url = f"/payment?applicant_id={applicant_id}"
        elif fee_hash:
            redirect_url = f"/payment?fee_id={fee_hash}"
        elif doctype == "Fees":
            # Try to get fee_hash from Fees document
            controller = frappe.get_last_doc("Easebuzz Settings")
            docname = controller.format_data(data.get("udf2"), reverse=True)
            fee_hash = frappe.db.get_value("Fees", docname, "fee_hash")
            if fee_hash:
                redirect_url = f"/payment?fee_id={fee_hash}"

    except Exception as e:
        frappe.logger("easebuzz").exception(e)
    finally:
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = redirect_url
