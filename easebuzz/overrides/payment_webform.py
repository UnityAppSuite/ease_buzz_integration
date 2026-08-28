import frappe
from frappe.website.doctype.web_form.web_form import WebForm
from payments.utils import get_payment_gateway_controller


# Registered via extend_doctype_class, not override_doctype_class. frappe v16
# composes Web Form as type("ExtendedWebForm", (*extensions, WebForm)), so this
# class must be a sibling of payments' PaymentWebForm, not its subclass -- a base
# cannot precede its own subclass in an MRO. Extensions are applied in reverse
# install order, so easebuzz (installed after payments) takes precedence and its
# get_payment_gateway_url wins, while payments' validate() is still inherited.
class CustomPaymentWebForm(WebForm):
    def get_payment_gateway_url(self, doc):
        if getattr(self, "accept_payment", False):
            controller = get_payment_gateway_controller(self.payment_gateway)

            title = f"Payment for {doc.doctype} {doc.name}"
            amount = self.amount
            if self.amount_based_on_field:
                amount = doc.get(self.amount_field)

            from decimal import Decimal

            if amount is None or Decimal(amount) <= 0:
                return frappe.utils.get_url(self.success_url or self.route)

            split_payments = {}
            if doc.school:
                bank_label = frappe.get_value("School", doc.school, "default_bank_label")
                label = frappe.get_value("Bank Account", bank_label, "account_name")
                split_payments[label] = amount

            payment_details = {
                "amount": amount,
                "title": title,
                "description": title,
                "reference_doctype": doc.doctype,
                "reference_docname": doc.name,
                "payer_email": frappe.session.user,
                "payer_name": frappe.utils.get_fullname(frappe.session.user),
                "order_id": doc.name,
                "currency": self.currency,
                "redirect_to": frappe.utils.get_url(self.success_url or self.route),
                "split_payments": split_payments,
            }

            # Redirect the user to this url
            return controller.get_payment_url_web_form(**payment_details)
