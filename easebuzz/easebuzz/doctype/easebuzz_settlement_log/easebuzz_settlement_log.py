import frappe
from frappe.model.document import Document
import json

class EasebuzzSettlementLog(Document):
    pass

def make_account_entry(account, debit, credit, against_account, cost_center,
                       currency="INR", exchange_rate=1):
    return {
        "account": account,
        "account_type": "",
        "cost_center": cost_center,
        "account_currency": currency,
        "exchange_rate": exchange_rate,
        "debit_in_account_currency": debit,
        "debit": debit,
        "credit_in_account_currency": credit,
        "credit": credit,
        "is_advance": "No",
        "against_account": against_account
    }

def get_account_and_company(label):
    account = frappe.db.get_value(
        "Bank Account", {'bank_account_no': label}, 'account'
    )
    company_name = frappe.db.get_value(
        "Bank Account", {'bank_account_no': label}, 'company'
    )
    if not company_name:
        frappe.throw(f"No Bank Account found with Easebuzz account number {label}")
    if not account:
        frappe.throw(f"No GL Account linked to Bank Account with account number {label}")
    company = frappe.get_doc("Company", company_name)
    return account, company

def create_journal_entry(title, company, posting_date, cheque_no, cheque_date,
                         remark, total_amount, accounts_data):
    je = frappe.new_doc("Journal Entry")
    je.update({
        "is_system_generated": 1,
        "title": title,
        "voucher_type": "Bank Entry",
        "naming_series": "ACC-JV-.YYYY.-",
        "company": company.name,
        "posting_date": posting_date,
        "cheque_no": cheque_no,
        "cheque_date": cheque_date,
        "user_remark": remark,
        "total_debit": total_amount,
        "total_credit": total_amount,
        "write_off_based_on": "Accounts Receivable",
        "write_off_amount": 0,
        "letter_head": "Default letter head",
        "mode_of_payment": "Online",
        "is_opening": "No",
        "repost_required": 0,
        "doctype": "Journal Entry",
    })
    for acc in accounts_data:
        je.append("accounts", acc)
    je.insert(ignore_permissions=True)
    je.submit()

def process_log(doc, method=None):
    try:
        if isinstance(doc.data, str) and doc.data.startswith("{'"):
            import ast
            doc_dict = ast.literal_eval(doc.data)
            data = json.loads(doc_dict['data'])
        else:
            data = json.loads(doc.data)

        # 1) Settlement payouts
        for split in data.get('split_payouts', []):
            label = split.get('account_number')
            amount = split.get('payout_amount', 0)
            bank_acc, company = get_account_and_company(label)

            accounts = [
                make_account_entry(
                    bank_acc, amount, 0,
                    company.default_easebuzz_account,
                    company.cost_center
                ),
                make_account_entry(
                    company.default_easebuzz_account, 0, amount,
                    bank_acc,
                    company.cost_center
                )
            ]

            create_journal_entry(
                title="Easebuzz Settlement",
                company=company,
                posting_date=split.get('payout_date'),
                cheque_no=split.get('bank_transaction_id'),
                cheque_date=split.get('payout_date'),
                remark="Easebuzz Settlement",
                total_amount=amount,
                accounts_data=accounts
            )

        # 2) Charges entries
        for txn in data.get('settled_transactions', []):
            if txn.get('transaction_type') in ('Netbanking', 'UPI'):
                fee_amount = 0
                for st in txn.get('split_transactions', []):
                    fee_amount += st.get('service_charge', 0) + st.get('service_tax', 0)
                if not fee_amount:
                    continue

                for split in txn.get('split_transactions', []):
                    label = split.get('account_number')
                    bank_acc, company = get_account_and_company(label)

                    accounts = [
                        make_account_entry(
                            company.custom_easebuzz_charges,
                            fee_amount, 0,
                            bank_acc,
                            company.cost_center
                        ),
                        make_account_entry(
                            bank_acc, 0,
                            fee_amount,
                            company.custom_easebuzz_charges,
                            company.cost_center
                        )
                    ]

                    create_journal_entry(
                        title="Easebuzz Settlement Charges",
                        company=company,
                        posting_date=frappe.utils.nowdate(),
                        cheque_no=txn.get('txnid'),
                        cheque_date=frappe.utils.nowdate(),
                        remark=f"Easebuzz charges - easepayid:{txn.get('easepayid')}",
                        total_amount=fee_amount,
                        accounts_data=accounts
                    )

    except Exception as e:
        frappe.logger('ease').exception(e)
