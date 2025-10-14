# Copyright (c) 2023, Hybrowlabs and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document
from easebuzz.easebuzz.utils.easebuzz_payment_gateway import Easebuzz
from frappe.utils import call_hook_method
from frappe.utils.data import cint
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
            show_payment_mode = get_payment_mode(payment_method)
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
                "show_payment_mode": show_payment_mode,
                "udf1": f"{doctype}",  # Payment Request Doctype
                "udf2": f"{docname}",  # Payment Request Docname
                "udf3": "",
                "udf4": "",
                "udf5": "",
            }
            if self.enable_split_payment:
                postDict["split_payments"] = split_payments
            if self.enable_sub_merchant:
                postDict["sub_merchant_id"] = self.get_sub_merchant_id(school=student.school)
            frappe.logger('ease_settle').exception(postDict)
            url = self.client.initiatePaymentAPI(postDict)
            return url
        except Exception as e:
            frappe.logger("ease_url").exception(e)
            return str(e)
        
    def get_sub_merchant_id(self, school=None, student=None):
        if school:
            filters = {"reference_doctype": "School", "reference_name": school}
            return frappe.get_cached_value("Easebuzz Sub Merchant", filters, "merchant_id")
        if student:
            school = frappe.get_cached_value("Student", student, "school")
            filters = {"reference_doctype": "School", "reference_name": school}
            return frappe.get_cached_value("Easebuzz Sub Merchant", filters, "merchant_id")
        return None

    def get_payment_url_web_form(self, **kwargs):
        """
        This function is called from the web form to get the payment url
        """
        try:
            doctype = kwargs.get("reference_doctype")
            docname = kwargs.get("reference_docname")
            doc = frappe.get_doc(doctype, docname)
            docname = docname.replace("(", "@").replace(")", "#")
            if doctype == "Student Applicant":
                student = doc
            else:
                student = frappe.get_doc("Student", doc.student)
            site_url = frappe.utils.get_url()
            amounts = float(kwargs.get("amount"))
            title = f"Payment for {doctype} {student.name} - {student.first_name}"

            payment_method = str(kwargs.get("payment_method"))
            show_payment_mode = get_payment_mode(payment_method)
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
                "email": student.student_email_id or f"{kwargs.get('payer_email')}",
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
                "show_payment_mode": show_payment_mode,
                "udf1": f"{doctype}",  # Doctype
                "udf2": f"{docname}",  # Docname
                "udf3": "webform",
                "udf4": "",
                "udf5": "",
            }
            if self.enable_split_payment:
                postDict["split_payments"] = split_payments
            if self.enable_sub_merchant:
                postDict["sub_merchant_id"] = self.get_sub_merchant_id(school=student.school)
            frappe.logger("ease_settle").exception(postDict)
            url = self.client.initiatePaymentAPI(postDict)
            return url
        except Exception:
            frappe.log_error(
                "Error while Generating Payment Link", frappe.get_traceback()
            )


    def process_name(self,name):
        return ''.join(c for c in name if c.isalnum())

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
        payment_request_doctype = data.get("udf1")
        payment_request_docname = data.get("udf2")
        status = data.get("status")
        transaction_id = data.get("txnid")
        if status == "success":
            if frappe.db.exists(payment_request_doctype, payment_request_docname):
                frappe.msgprint("Payment Request exists")
                payment_request = frappe.get_doc(
                    payment_request_doctype,
                    payment_request_docname,
                    ignore_permissions=True,
                )
                frappe.db.set_value(
                    payment_request_doctype,
                    payment_request_docname,
                    "transaction_id",
                    transaction_id,
                )
                payment_request.on_payment_authorized(status="Completed")
                return {"message": "Payment Successful"}
            else:
                frappe.msgprint("Payment Request does not exist, Invalid Request")

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
                if hasattr(doc, "validate_payment"):
                    return doc.validate_payment(data)
                else:
                    return {"message": "Payment Successful"}
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
    return payment_methods.get(method.lower(), "")


def get_surchage():
    fee_setting = frappe.get_single("Fees Settings")
    return fee_setting.surcharge
