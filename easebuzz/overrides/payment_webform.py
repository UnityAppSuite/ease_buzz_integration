import frappe
from payments.overrides.payment_webform import PaymentWebForm
from payments.utils import get_payment_gateway_controller


class CustomPaymentWebForm(PaymentWebForm):
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
                "webform": True,
            }

            # Redirect the user to this url
            return controller.get_payment_url(**payment_details)
