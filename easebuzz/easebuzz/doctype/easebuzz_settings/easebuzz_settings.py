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
        amounts = float(kwargs.get("amount"))

        payment_method = str(kwargs.get("payment_method"))
        show_payment_mode = (
            get_payment_mode(payment_method) if get_payment_mode(payment_method) else ""
        )
        split_payments = get_split_payment(fees)

        if get_surchage() == 1:
            charge = frappe.db.get_value(
                "Payment Methods", {"method": payment_method}, "charge"
            )
            total_amount = get_total_amount(amounts, charge)
            split_payments = get_split_payment_with_charge(
                split_payments, amounts, charge
            )
            surcharge = "enabled"
        else:
            total_amount = amounts
            surcharge = "disabled"

        postDict = {
            "txnid": f"{str(uuid.uuid4())[:8]}",
            "firstname": student.first_name,
            "phone": student.student_mobile_number,
            "email": f"{kwargs.get('payer_email')}",
            "amount": f"{total_amount}",
            "productinfo": payment_request.subject,
            "surl": f"{site_url}/easebuzz/success",
            "furl": f"{site_url}/easebuzz/failure",
            "city": student.city,
            "zipcode": student.pincode,
            "address2": student.address_line_2,
            "state": student.state,
            "address1": student.address_line_2,
            "country": student.country,
            "split_payments": split_payments,
            "show_payment_mode": show_payment_mode,
            "surcharge": surcharge,
            "udf1": f"{doctype}",  # Payment Request Doctype
            "udf2": f"{docname}",  # Payment Request Docname
            "udf3": "",
            "udf4": "",
            "udf5": "",
        }
        url = self.client.initiatePaymentAPI(postDict)
        return url

    # every fee type is linked with a bank account and the split of amount should go that way

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
        if status == "success":
            if frappe.db.exists(payment_request_doctype, payment_request_docname):
                frappe.msgprint("Payment Request exists")
                payment_request = frappe.get_doc(
                    payment_request_doctype, payment_request_docname
                )
                payment_request.on_payment_authorized(status="Completed")
                return {"message": "Payment Successful"}
            else:
                frappe.msgprint("Payment Request does not exist, Invalid Request")


@frappe.whitelist(allow_guest=True)
def get_merchant_key():
    controller = frappe.get_doc("EaseBuzz Settings")
    return controller.merchant_key


def get_split_payment(doc):
    try:
        fee = {i.fees_category: i.amount for i in doc.components}
        sp = frappe.get_single("Split Payment")
        accounts = {i.fee_category: i.label.split()[0] for i in sp.easebuzz_accounts}
        remaining_amount = 0
        split_payment = dict()
        for i in fee.keys():
            account_name = accounts.get(i)
            if account_name is not None:
                split_payment[account_name] = fee[i]
            else:
                remaining_amount += fee[i]

        default_account = sp.default_account.split()[0]
        if split_payment.get(default_account) is not None:
            split_payment[default_account] += remaining_amount
        else:
            split_payment[default_account] = remaining_amount
        return split_payment
    except Exception as e:
        frappe.log_error(e)


def get_payment_mode(method):
    payment_methods = {
        "net banking": "NB",
        "credit card": "CC",
        "debit card": "DC",
        "mobile wallet": "MW",
        "upi": "UPI",
    }
    return payment_methods.get(method.lower())


def get_total_amount(amount, charge):
    if amount is None:
        return 0

    if charge is None:
        return amount

    charge_amount = (amount * float(charge)) / 100
    total_amount = amount + charge_amount
    return total_amount


def get_split_payment_with_charge(split_payment, amount, charge):
    if charge is None:
        return split_payment

    charge_amount = (amount * float(charge)) / 100
    sp = frappe.get_single("Split Payment")
    default_account = sp.default_account.split()[0]
    if split_payment.get(default_account) is not None:
        split_payment[default_account] += charge_amount
    else:
        split_payment[default_account] = charge_amount
    return split_payment


def get_surchage():
    fee_setting = frappe.get_single("Fees Settings")
    return fee_setting.surcharge