# Copyright (c) 2023, Hybrowlabs and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.auth import LoginManager
from frappe.model.document import Document
from easebuzz.easebuzz.utils.easebuzz_payment_gateway import Easebuzz
from frappe.utils import call_hook_method
from frappe.utils.data import cint, flt
from payments.utils.utils import create_payment_gateway


class EasebuzzSettings(Document):
    supported_currencies = ["INR"]


    def init_client(self, surcharge):
        settings = frappe.get_doc("Easebuzz Settings", {"surcharge": surcharge})
        salt = settings.get_password(fieldname="salt", raise_exception=False)
        self.client = Easebuzz(settings.merchant_key, salt, settings.env)

    def after_insert(self):
        create_payment_gateway("Easebuzz", "Easebuzz Settings", self.name)
        call_hook_method("payment_gateway_enabled", gateway="Easebuzz")
      
    def validate_transaction_currency(self, currency):
        if currency not in self.supported_currencies:
            frappe.throw(
                frappe._(
                    "Please select another payment method. Easebuzz does not support transactions in currency '{0}'"
                ).format(currency)
            )

    def get_payment_url(self, **kwargs):
        try:
            doctype = kwargs.get("reference_doctype")
            docname = kwargs.get("reference_docname")
            payment_request = frappe.get_doc(doctype, docname)
            fee_doctype = payment_request.reference_doctype
            fee_docname = payment_request.reference_name
            fees = frappe.get_doc(fee_doctype, fee_docname)
            fees.reload()
            student = frappe.get_doc("Student", fees.student)
            site_url = frappe.utils.get_url()
            amounts = float(kwargs.get("amount"))

            payment_method = str(kwargs.get("payment_method"))
            show_payment_mode = (
                get_payment_mode(payment_method) if get_payment_mode(payment_method) else ""
            )
            if show_payment_mode in ["CC", "DC"]:
                self.init_client(surcharge=1)
            else:
                self.init_client(surcharge=0)
            split_payments = get_split_payment(fees, payment_request.payment_term)
            # print(split_payments)

            transaction_id = frappe.generate_hash(length=40)
            productinfo = "Payment Request for " + student.first_name
            mobile_number = student.student_mobile_number
            mobile_number = mobile_number if mobile_number else "9999999999"
            postDict = {
                "txnid": transaction_id,
                "firstname": self.process_name(student.first_name),
                "phone": mobile_number,
                "email": f"{kwargs.get('payer_email')}",
                "amount": f"{amounts}",
                "productinfo": productinfo,
                "surl": f"{site_url}/easebuzz/success?hash=" + payment_request.payment_hash,
                "furl": f"{site_url}/easebuzz/failure",
                "city": student.city,
                "zipcode": student.pincode,
                "address1": student.address_line_1,
                "address2": student.address_line_2,
                "state": student.state,
                "country": student.country,
                "split_payments": split_payments,
                "show_payment_mode": show_payment_mode,
                "udf1": f"{doctype}",  # Payment Request Doctype
                "udf2": f"{docname}",  # Payment Request Docname
                "udf3": "",
                "udf4": "",
                "udf5": "",
            }
            frappe.logger('ease_settle').exception(postDict)
            url = self.client.initiatePaymentAPI(postDict)
            return url
        except Exception as e:
            frappe.logger("ease_url").exception(e)
            return str(e)

    def get_payment_url_web_form(self, **kwargs):
        """
        This function is called from the web form to get the payment url
        """
        try:
            doctype = kwargs.get("reference_doctype")
            docname = kwargs.get("reference_docname")
            doc = frappe.get_doc(doctype, docname)
            docname = docname.replace("(", "@").replace(")", "#")
            student = frappe.get_doc("Student", doc.student)
            site_url = frappe.utils.get_url()
            amounts = float(kwargs.get("amount"))
            title = f"Payment for {doctype} {student.name} - {student.student_name}"

            payment_method = str(kwargs.get("payment_method"))
            show_payment_mode = (
                get_payment_mode(payment_method)
                if get_payment_mode(payment_method)
                else ""
            )
            if show_payment_mode in ["CC", "DC"]:
                self.init_client(surcharge=1)
            else:
                self.init_client(surcharge=0)

            split_payments = kwargs.get("split_payments", {})

            transaction_id = frappe.generate_hash(length=40)
            postDict = {
                "txnid": transaction_id,
                "firstname": self.process_name(student.first_name),
                "phone": student.student_mobile_number or "9999999999",
                "email": f"{kwargs.get('payer_email')}",
                "amount": f"{amounts}",
                "productinfo": title,
                "surl": f"{site_url}/easebuzz/success",
                "furl": f"{site_url}/easebuzz/failure",
                "city": student.city,
                "zipcode": student.pincode,
                "address1": student.address_line_1,
                "address2": student.address_line_2,
                "state": student.state,
                "country": student.country,
                "split_payments": split_payments,
                "show_payment_mode": show_payment_mode,
                "udf1": f"{doctype}",  # Doctype
                "udf2": f"{docname}",  # Docname
                "udf3": "webform",
                "udf4": "",
                "udf5": "",
            }
            frappe.logger("ease_settle").exception(postDict)
            url = self.client.initiatePaymentAPI(postDict)
            return url
        except Exception:
            frappe.log_error(
                "Error while Generating Payment Link", frappe.get_traceback()
            )

    def get_payment_url_applicant(self, **kwargs):
        """Generate payment URL for Student Applicant deposit payment."""
        try:
            applicant_id = kwargs.get("applicant_id")
            applicant = frappe.get_doc("Student Applicant", applicant_id)
            site_url = frappe.utils.get_url()

            student_name = kwargs.get("student_name") or f"{applicant.first_name} {applicant.last_name or ''}".strip()
            payment_method = kwargs.get("payment_method") or ""
            show_payment_mode = get_payment_mode(payment_method) if payment_method else ""

            self.init_client(surcharge=1 if show_payment_mode in ["CC", "DC"] else 0)

            postDict = {
                "txnid": frappe.generate_hash(length=40),
                "firstname": self.process_name(applicant.first_name or "Applicant"),
                "phone": kwargs.get("payer_phone") or applicant.student_mobile_number or "9999999999",
                "email": kwargs.get("payer_email") or applicant.student_email_id,
                "amount": f"{float(kwargs.get('amount'))}",
                "productinfo": f"Deposit Payment for {student_name}",
                "surl": f"{site_url}/easebuzz/success",
                "furl": f"{site_url}/easebuzz/failure",
                "city": applicant.city or "",
                "zipcode": applicant.pincode or "",
                "address1": applicant.address_line_1 or "",
                "address2": applicant.address_line_2 or "",
                "state": applicant.state or "",
                "country": applicant.country or "India",
                "split_payments": kwargs.get("split_payments", ""),
                "show_payment_mode": show_payment_mode,
                "udf1": "Student Applicant",
                "udf2": applicant_id,
                "udf3": "applicant",
                "udf4": "",
                "udf5": "",
            }
            return self.client.initiatePaymentAPI(postDict)
        except Exception as e:
            frappe.log_error(f"Error generating Applicant Payment Link: {str(e)}", frappe.get_traceback())
            return None

    def process_name(self,name):
        return ''.join(c for c in name if c.isalnum())
    
    def format_data(self, value, reverse=False):
        """
        Format data for payment gateway compatibility.
        Replaces '(' with '@' and ')' with '#' when reverse is False,
        and vice versa when reverse is True.
        """
        if not value or not isinstance(value, str):
            return value or ""
        if reverse:
            return value.replace("@", "(").replace("#", ")").strip()
        return value.strip().replace("(", "@").replace(")", "#")

    def get_settings(self, data):
        settings = frappe._dict(
            {
                "merchant_key": self.merchant_key,
                "salt": self.get_password(fieldname="salt", raise_exception=False),
            }
        )

        if cint(data.get("notes", {}).get("use_sandbox")) or data.get("use_sandbox"):
            settings.update(
                {
                    "merchant_key": frappe.conf.sandbox_merchant_key,
                    "salt": frappe.conf.sandbox_salt,
                }
            )

        return settings

    def handle_response(self, data):
        """
        Handle the response from the Easebuzz payment gateway
        """
        try:
            # TODO: need to create a new user for this purpose
            login_manager = LoginManager()
            login_manager.login_as("Administrator")
            
            # Extract and validate required data
            doctype = data.get("udf1")
            docname = self.format_data(data.get("udf2"), reverse=True)
            payment_term = data.get("udf3")
            status = data.get("status")
            amount = data.get("amount")
            transaction_id = data.get("txnid")
            
            if status != "success":
                return {"message": "Payment Validation Failed"}
            
            # Validate document exists
            if not frappe.db.exists(doctype, docname):
                frappe.log_error(f"{doctype} {docname} does not exist")
                return {"message": "Document not found"}
            
            # Process payment based on doctype
            doc = frappe.get_doc(doctype, docname, ignore_permissions=True)
            
            if doctype == "Fees":
                doc.on_payment_authorized(
                    status="Completed",
                    payment_term=payment_term,
                    transaction_id=transaction_id,
                    amount=amount
                )
            elif doctype == "Payment Request":
                doc.on_payment_authorized(status="Completed")
            elif doctype == "Student Applicant":
                result = doc.on_payment_authorized(
                    status="Completed",
                    transaction_id=transaction_id,
                    amount=amount
                )
                frappe.logger("easebuzz").info(f"Applicant payment processed: {result}")
                return result
            else:
                frappe.log_error(f"Unsupported doctype: {doctype} name: {docname}")
                return {"message": "Unsupported document type"}
            
            return {"message": "Payment Successful"}
            
        except Exception as e:
            frappe.log_error("Error in handle_response", frappe.get_traceback())
            return {"message": "Payment processing failed"}
        finally:
            login_manager.logout()

    def handle_response_web_form(self, data):
        doctype = data.get("udf1")
        docname = data.get("udf2")
        docname = docname.replace("@", "(").replace("#", ")")
        status = data.get("status")
        transaction_id = data.get("txnid")
        if status == "success":
            if frappe.db.exists(doctype, docname):
                frappe.db.set_value(doctype, docname, "transaction_id", transaction_id)
                doc = frappe.get_doc(doctype, docname, ignore_permissions=True)
                return doc.validate_payment(data)
            else:
                frappe.log_error(f"{doctype} {docname} does not exist")

    def initiateRefund(self, data):
        amounts = float(data.get("amount"))
        refund_amount = float(data.get("refund_amount"))
        self.init_client(surcharge=0)
        transaction_id = data.get("transaction_id")
        postDict = {
            "txnid": f"{transaction_id}",
            "refund_amount": f"{refund_amount}",
            "phone": f"{data.get('phone')}",
            "email": f"{data.get('email')}",
            "amount": f"{amounts}",
        }
        response = self.client.refundAPI(postDict)
        return response


    def generate_payment_url(self, **kwargs):
        try:
            # Initialize the Easebuzz client
            salt = self.get_password(fieldname="salt", raise_exception=False)
            self.client = Easebuzz(self.merchant_key, salt, self.env)
            # Validate the student and retrieve necessary details
            student = frappe.get_doc("Student", kwargs.get("student"))
            site_url = frappe.utils.get_url()
            amount = flt(kwargs.get("amount", 0))
            transaction_id = frappe.generate_hash(length=40)
            fee_hash = kwargs.get("fee_hash", "")
            email = student.student_email_id
            payment_plan = kwargs.get("payment_plan", "")
            reference_name = kwargs.get("reference_docname", "")
            first_name = self.process_name(student.first_name)
            # Prepare the post data for payment initiation
            post_data = {
                "txnid": transaction_id,
                "firstname": first_name,
                "phone": student.student_mobile_number or "9999999999",
                "email": email,
                "city": student.city or "",
                "zipcode": student.pincode or "",
                "address1": student.address_line_1 or "",
                "address2": student.address_line_2 or "",
                "state": student.state or "",
                "country": student.country or "",
                "amount": str(amount),
                "productinfo": f"Payment Request for {first_name}",
                "surl": kwargs.get("success_url") or f"{site_url}/easebuzz/success",
                "furl": kwargs.get("failure_url") or f"{site_url}/easebuzz/failure",
                "show_payment_mode": get_payment_mode(kwargs.get("payment_method")),
                "udf1": kwargs.get("reference_doctype", ""),
                "udf2": self.format_data(reference_name),
                "udf3": kwargs.get("payment_term", ""),
                "udf4": self.format_data(payment_plan),
                "udf5": fee_hash,
            }
            # Process split payments if provided
            split_payments = kwargs.get("split_payments")
            if split_payments:
                post_data["split_payments"] = split_payments

            return self.client.initiatePaymentAPI(post_data)

        except Exception:
            frappe.log_error("Error in generate_payment_url", frappe.get_traceback())
            return None

@frappe.whitelist(allow_guest=True)
def get_merchant_key():
    controller = frappe.get_doc("Easebuzz Settings")
    return controller.merchant_key


def get_split_payment(fees, term=None):
    try:
        split_payments = json.loads(fees.split_payments)
        if term:
            return split_payments.get(term)
        else:
            return split_payments.get("Deposit")
    except Exception as e:
        frappe.logger("split_payment").exception(e)
        return ""


def get_payment_mode(method):
    payment_methods = {
        "net banking": "NB",
        "credit card": "CC",
        "debit card": "DC",
        "mobile wallet": "MW",
        "upi": "UPI",
    }
    return payment_methods.get(method.lower()) or ""


def get_surchage():
    fee_setting = frappe.get_single("Fees Settings")
    return fee_setting.surcharge
