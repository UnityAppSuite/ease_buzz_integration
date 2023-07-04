# Copyright (c) 2023, Hybrowlabs and contributors
# For license information, please see license.txt

import uuid
import frappe
from frappe.model.document import Document
from easebuzz.easebuzz.utils.easebuzz_payment_gateway import Easebuzz
from frappe.utils import call_hook_method
from frappe.utils.data import cint
from payments.utils.utils import create_payment_gateway


class EaseBuzzSettings(Document):
    supported_currencies = ["INR"]

    def init_client(self):
        if self.merchant_key:
            salt = self.get_password(fieldname="salt", raise_exception=False)
            self.client = Easebuzz(self.merchant_key, salt, self.env)

    def validate(self):
        create_payment_gateway("EaseBuzz")
        call_hook_method("payment_gateway_enabled", gateway="EaseBuzz")

    def validate_transaction_currency(self, currency):
        if currency not in self.supported_currencies:
            frappe.throw(
                frappe._(
                    "Please select another payment method. EaseBuzz does not support transactions in currency '{0}'"
                ).format(currency)
            )

    def get_payment_url(self, **kwargs):
        doctype = kwargs.get("reference_doctype")
        docname = kwargs.get("reference_docname")
        payment_request = frappe.get_doc(doctype, docname)
        fee_doctype = payment_request.reference_doctype
        fee_docname = payment_request.reference_name
        fees = frappe.get_doc(fee_doctype, fee_docname)
        student = frappe.get_doc("Student", fees.student)
        self.init_client()
        site_url = frappe.utils.get_url()
        postDict = {
            "txnid": f"{str(uuid.uuid4())[:8]}",
            "firstname": f"{kwargs.get('payer_name')}",
            "phone": student.student_mobile_number,
            "email": f"{kwargs.get('payer_email')}",
            "amount": f"{kwargs.get('amount')}",
            "productinfo": payment_request.subject,
            "surl": f"{site_url}/success",
            "furl": f"{site_url}/failure",
            "city": student.city,
            "zipcode": student.pincode,
            "address2": student.address_line_2,
            "state": student.state,
            "address1": student.address_line_2,
            "country": student.country,
            "udf1": f"{fee_doctype}",
            "udf2": f"{fee_docname}",
            "udf3": "",
            "udf4": "",
            "udf5": "",
        }
        url = self.client.initiatePaymentAPI(postDict)
        return url

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


@frappe.whitelist(allow_guest=True)
def get_merchant_key():
    controller = frappe.get_doc("EaseBuzz Settings")
    return controller.merchant_key
