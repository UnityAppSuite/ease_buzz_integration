from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from easebuzz.easebuzz.doctype.easebuzz_settings.easebuzz_settings import EasebuzzSettings


class TestPaymentURLValidation(FrappeTestCase):
    def test_missing_payer_email_is_explained_without_contacting_gateway(self):
        settings = EasebuzzSettings({"doctype": "Easebuzz Settings", "merchant_key": "test-key", "env": "test"})
        student = frappe._dict(first_name="UAT", student_email_id=None, student_mobile_number=None)

        with (
            patch.object(settings, "get_password", return_value="test-salt"),
            patch("easebuzz.easebuzz.doctype.easebuzz_settings.easebuzz_settings.frappe.get_doc", return_value=student),
            patch("easebuzz.easebuzz.doctype.easebuzz_settings.easebuzz_settings.Easebuzz.initiatePaymentAPI") as initiate,
        ):
            with self.assertRaisesRegex(frappe.ValidationError, "email"):
                settings.generate_payment_url(student="UAT-STUDENT", amount=50000)
            initiate.assert_not_called()

    def test_payer_email_is_passed_to_gateway_when_student_email_is_missing(self):
        settings = EasebuzzSettings({"doctype": "Easebuzz Settings", "merchant_key": "test-key", "env": "test"})
        student = frappe._dict(first_name="UAT", student_email_id=None, student_mobile_number=None)

        with (
            patch.object(settings, "get_password", return_value="test-salt"),
            patch("easebuzz.easebuzz.doctype.easebuzz_settings.easebuzz_settings.frappe.get_doc", return_value=student),
            patch("easebuzz.easebuzz.doctype.easebuzz_settings.easebuzz_settings.Easebuzz.initiatePaymentAPI", return_value="https://testpay.easebuzz.in/pay/123") as initiate,
        ):
            url = settings.generate_payment_url(
                student="UAT-STUDENT", amount=50000, payer_email="payer@example.com"
            )

        self.assertEqual(url, "https://testpay.easebuzz.in/pay/123")
        self.assertEqual(initiate.call_args.args[0]["email"], "payer@example.com")

    def test_invalid_payer_email_is_rejected_before_gateway(self):
        settings = EasebuzzSettings({"doctype": "Easebuzz Settings", "merchant_key": "test-key", "env": "test"})
        student = frappe._dict(first_name="UAT", student_email_id=None, student_mobile_number=None)

        with (
            patch.object(settings, "get_password", return_value="test-salt"),
            patch("easebuzz.easebuzz.doctype.easebuzz_settings.easebuzz_settings.frappe.get_doc", return_value=student),
            patch("easebuzz.easebuzz.doctype.easebuzz_settings.easebuzz_settings.Easebuzz.initiatePaymentAPI") as initiate,
        ):
            for email in ("not-an-email", "  ", "a@example.com,b@example.com"):
                with self.subTest(email=email), self.assertRaises(frappe.ValidationError):
                    settings.generate_payment_url(student="UAT-STUDENT", amount=50000, payer_email=email)
            initiate.assert_not_called()
