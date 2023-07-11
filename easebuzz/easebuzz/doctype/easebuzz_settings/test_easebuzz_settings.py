# Copyright (c) 2023, Hybrowlabs and Contributors
# See license.txt

import uuid
import frappe
from frappe.tests.utils import FrappeTestCase
from easebuzz.easebuzz.utils.easebuzz_payment_gateway import Easebuzz


def create_easebuzz_settings():
    if frappe.flags.test_events_created:
        return

    frappe.set_user("Administrator")
    doc = frappe.get_doc(
        {
            "doctype": "EaseBuzz Settings",
            "merchant_key": "2PBP7IABZ2",
            "salt": "DAH88E3UWQ",
            "env": "test",
        }
    ).insert()
    frappe.flags.test_events_created = True


def get_payment_url():
    doc = frappe.get_doc("EaseBuzz Settings")
    salt = doc.get_password(fieldname="salt", raise_exception=False)
    easebuzz = Easebuzz(doc.merchant_key, salt, doc.env)
    site_url = frappe.utils.get_url()
    postDict = {
            "txnid": f"{str(uuid.uuid4())[:8]}",
            "firstname": "Test name",
            "phone": "9970384057",
            "email": "reva99703@walnut.edu",
            "amount": "50.0",
            "productinfo": "Test Info",
            "surl": f"{site_url}/easebuzz/success",
            "furl": f"{site_url}/easebuzz/failure",
            "city": "Pune",
            "zipcode": "411057",
            "address1": ", Chatrapati chowk Wakad Pune 411057, ,",
            "address2": ", Chatrapati chowk Wakad Pune 411057, ,",
            "state": "Maharashtra",
            "country": "India",
            "udf1": "", 
            "udf2": "", 
            "udf3": "",
            "udf4": "",
            "udf5": "",
        }
    url = easebuzz.initiatePaymentAPI(postDict)
    return url


class TestEaseBuzzSettings(FrappeTestCase):
    def setUp(self):
        create_easebuzz_settings()

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_payment_link_generation(self):
        expected_url = "https://testpay.easebuzz.in/pay"
        actual_url = get_payment_url()
        actual_base_url = actual_url.rsplit("/", 1)[0]
        self.assertEqual(expected_url, actual_base_url)