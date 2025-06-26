# Copyright (c) 2024, Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json

class EasebuzzSettlementLog(Document):
	pass

def process_log(doc,method=None):
	#try:
	#data = doc.data[25:-73]
	data = json.loads(doc.data)
	for split in data.get('split_payouts'):
		label = split.get("bank_account_no")
		company = frappe.db.get_value(
			"Bank Account",
			{'bank_account_no':label},
			'company'
		)
		if not company:
			frappe.throw(f"No Bank Account found with Easebuzz account number {label}")
		company = frappe.get_doc("Company",company)
		je = frappe.new_doc("Journal Entry")
		amount = split.get('payout_amount')
		account = frappe.db.get_value("Bank Account",{'bank_account_no':label},'account')
		je.update({
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
		})
		je.append("accounts",
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
					"against_account": company.default_easebuzz_account
					})
		je.append("accounts",
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
					"against_account": account
					})
		je.insert(ignore_permissions=True)
		je.submit()
	for settled_transaction in data.get('settled_transactions'):
		if settled_transaction.get('transaction_type') in ('Netbanking','UPI'):
			for split_transaction in settled_transaction.get('split_transactions'):
				label = split_transaction.get("bank_account_no")
				company = frappe.db.get_value(
					"Bank Account",
					{'bank_account_no':label},
					'company'
				)
				if not company:
					frappe.throw(f"No Bank Account found with Easebuzz account number {label}")
				company = frappe.get_doc("Company",company)
				je = frappe.new_doc("Journal Entry")
				fee_amount = split_transaction.get('service_charge', 0) + split_transaction.get("service_tax", 0)
				if not fee_amount:
					continue	
				je.update({
					"is_system_generated": 1,
					"title": "Easebuzz Settlement Charges",
					"voucher_type": "Bank Entry",
					"naming_series": "ACC-JV-.YYYY.-",
					"company": company.name,
					"posting_date": frappe.utils.nowdate(),
					"cheque_no": settled_transaction.get("txnid"),
					"cheque_date": frappe.utils.nowdate(),
					"user_remark": "Easebuzz charges - easepayid:" + settled_transaction.get("easepayid"),
					"total_debit": fee_amount,
					"total_credit": fee_amount,
					"write_off_based_on": "Accounts Receivable",
					"write_off_amount": 0,
					"letter_head": "Default letter head",
					"mode_of_payment": "Online",
					"is_opening": "No",
					"repost_required": 0,
					"doctype": "Journal Entry",
				})
				je.append("accounts",
					{
							"account": company.custom_easebuzz_charges,
							"account_type": "",
							"cost_center": company.cost_center,
							"account_currency": "INR",
							"exchange_rate": 1,
							"debit_in_account_currency": fee_amount,
							"debit": fee_amount,
							"credit_in_account_currency": 0,
							"credit": 0,
							"is_advance": "No",
							"against_account": company.default_easebuzz_account
							})
				je.append("accounts",
					{
							"account": company.default_easebuzz_account,
							"account_type": "",
							"cost_center": company.cost_center,
							"account_currency": "INR",
							"exchange_rate": 1,
							"debit_in_account_currency": 0,
							"debit": 0,
							"credit_in_account_currency": fee_amount,
							"credit": fee_amount,
							"is_advance": "No",
							"against_account": company.custom_easebuzz_charges
							})
				je.insert(ignore_permissions=True)
				je.submit()
	#except Exception as e:
	#frappe.logger('ease').exception(e)