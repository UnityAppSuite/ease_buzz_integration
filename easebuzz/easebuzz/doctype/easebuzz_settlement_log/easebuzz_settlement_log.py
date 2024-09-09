# Copyright (c) 2024, Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class EasebuzzSettlementLog(Document):
    pass


def process_log(doc, method=None):
    try:

        data = doc.data[25:-73]
        data = json.loads(data)
        frappe.logger("ease").exception(Exception(str(data)))
        for split in data.get("split_payouts"):
            label = split.get("account_label")
            company = frappe.db.get_value(
                "Bank Account", {"account_name": label}, "company"
            )
            company = frappe.get_doc("Company", company)
            je = frappe.new_doc("Journal Entry")
            amount = split.get("payout_amount")
            account = frappe.db.get_value(
                "Bank Account", {"account_name": label}, "account"
            )

            je.update(
                {
                    "is_system_generated": 1,
                    "title": "Easebuzz Settlement",
                    "voucher_type": "Bank Entry",
                    "naming_series": "ACC-JV-.YYYY.-",
                    "company": company.name,
                    "posting_date": split.get("payout_date"),
                    "cheque_no": split.get("bank_transaction_id"),
                    "cheque_date": split.get("payout_date"),
                    "user_remark": "Easebuzz Settlement",
                    "total_debit": amount,
                    "total_credit": amount,
                    "write_off_based_on": "Accounts Receivable",
                    "write_off_amount": 0,
                    "letter_head": "Default letter head",
                    "mode_of_payment": "Online",
                    "is_opening": "No",
                    "repost_required": 0,
                    "doctype": "Journal Entry",
                }
            )
            je.append(
                "accounts",
                {
                    "account": account,
                    "account_type": "",
                    "cost_center": company.cost_center,
                    "account_currency": "INR",
                    "exchange_rate": 1,
                    "debit_in_account_currency": amount,
                    "debit": amount,
                    "credit_in_account_currency": 0,
                    "credit": 0,
                    "is_advance": "No",
                    "against_account": company.default_easebuzz_account,
                },
            )
            je.append(
                "accounts",
                {
                    "account": company.default_easebuzz_account,
                    "account_type": "",
                    "cost_center": company.cost_center,
                    "account_currency": "INR",
                    "exchange_rate": 1,
                    "debit_in_account_currency": 0,
                    "debit": 0,
                    "credit_in_account_currency": amount,
                    "credit": amount,
                    "is_advance": "No",
                    "against_account": account,
                },
            )
            je.save(ignore_permissions=True)
            je.submit()

        fees_settings_doc = frappe.get_doc("Fees Settings")

        settings_hash = {
            str(fees.get("method")).lower(): fees.get("easebuzz_account")
            for fees in fees_settings_doc.payment_method
        }

        for settled_transaction in data.get("settled_transactions"):
            transaction_type = settled_transaction.get("transaction_type")
            if settings_hash[str(transaction_type).lower()] == "Surcharge":
                for split_transaction in settled_transaction.get("split_transactions"):
                    label = split_transaction.get("account_label")
                    company = frappe.db.get_value(
                        "Bank Account", {"account_name": label}, "company"
                    )
                    company = frappe.get_doc("Company", company)
                    je = frappe.new_doc("Journal Entry")
                    amount = split_transaction.get(
                        "service_charge"
                    ) + split_transaction.get("service_tax")
                    je.update(
                        {
                            "is_system_generated": 1,
                            "title": "Easebuzz Settlement Charges",
                            "voucher_type": "Bank Entry",
                            "naming_series": "ACC-JV-.YYYY.-",
                            "company": company.name,
                            "posting_date": frappe.utils.nowdate(),
                            "cheque_no": settled_transaction.get("txnid"),
                            "cheque_date": frappe.utils.nowdate(),
                            "user_remark": "Easebuzz charges - easepayid:"
                            + settled_transaction.get("easepayid"),
                            "total_debit": amount,
                            "total_credit": amount,
                            "write_off_based_on": "Accounts Receivable",
                            "write_off_amount": 0,
                            "letter_head": "Default letter head",
                            "mode_of_payment": create_or_get_mode_of_payment(
                                transaction_type
                            ),
                            "is_opening": "No",
                            "repost_required": 0,
                            "doctype": "Journal Entry",
                        }
                    )
                    je.append(
                        "accounts",
                        {
                            "account": company.custom_easebuzz_charges,
                            "account_type": "",
                            "cost_center": company.cost_center,
                            "account_currency": "INR",
                            "exchange_rate": 1,
                            "debit_in_account_currency": amount,
                            "debit": amount,
                            "credit_in_account_currency": 0,
                            "credit": 0,
                            "is_advance": "No",
                            "against_account": company.default_easebuzz_account,
                        },
                    )
                    je.append(
                        "accounts",
                        {
                            "account": company.default_easebuzz_account,
                            "account_type": "",
                            "cost_center": company.cost_center,
                            "account_currency": "INR",
                            "exchange_rate": 1,
                            "debit_in_account_currency": 0,
                            "debit": 0,
                            "credit_in_account_currency": amount,
                            "credit": amount,
                            "is_advance": "No",
                            "against_account": company.custom_easebuzz_charges,
                        },
                    )
    except Exception as e:
        frappe.logger("ease").exception(e)


def create_or_get_mode_of_payment(mode_of_payment):
    name = frappe.db.exists("Mode of Payment", mode_of_payment)
    if name:
        return name
    mode_of_payment_doc = frappe.new_doc("Mode of Payment")
    mode_of_payment_doc.mode_of_payment = mode_of_payment
    mode_of_payment.type = "General"
    mode_of_payment_doc.insert(ignore_permissions=True)
    return mode_of_payment_doc.name
