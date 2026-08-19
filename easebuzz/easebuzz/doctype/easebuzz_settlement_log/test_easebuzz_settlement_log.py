# Copyright (c) 2026, Hybrowlabs and contributors
# See license.txt

import json
import unittest

from easebuzz.easebuzz.utils.settlement import (
    SettlementError,
    parse_settlement_payload,
    resolve_rule,
    segregate,
    validate_segregation,
)

SETTLEMENT = {
    "payout_id": "PTTEST0001",
    "payout_date": "2026-08-18 12:55:06.618976",
    "total_amount": 1118.88,
    "payout_amount": 1100.00,
    "service_charge_amount": 16.00,
    "service_tax_amount": 2.88,
    "split_payouts": [
        {
            "account_number": "50200011443440",
            "payout_amount": 700.00,
            "split_payout_id": "SPA",
            "account_label": "PrimaryTuitionFeeShivane",
            "bank_transaction_id": "YESB0001",
        },
        {
            "account_number": "50200080706351",
            "payout_amount": 400.00,
            "split_payout_id": "SPB",
            "account_label": "CurriculamMaterialFee",
            "bank_transaction_id": "YESB0002",
        },
    ],
    "settled_transactions": [
        {
            "transaction_type": "Netbanking",
            "split_transactions": [
                {"split_payout_id": "SPA", "service_charge": 8.00, "service_tax": 1.44},
            ],
        },
        {
            "transaction_type": "Credit Card",
            "split_transactions": [
                {"split_payout_id": "SPB", "service_charge": 8.00, "service_tax": 1.44},
            ],
        },
    ],
}


class TestSettlementPayloadParsing(unittest.TestCase):
    """``Settlement Log.data`` arrives in several shapes; all must reach the inner body."""

    def test_unwraps_python_repr_envelope(self):
        raw = repr(
            {
                "status": "1",
                "data": json.dumps(SETTLEMENT),
                "cmd": "edu_quality.edu_quality.server_scripts.utils.settlement_hook",
            }
        )
        self.assertEqual(parse_settlement_payload(raw)["payout_id"], "PTTEST0001")

    def test_unwraps_json_envelope(self):
        raw = json.dumps({"status": "1", "data": json.dumps(SETTLEMENT)})
        self.assertEqual(parse_settlement_payload(raw)["payout_id"], "PTTEST0001")

    def test_accepts_bare_settlement_json(self):
        parsed = parse_settlement_payload(json.dumps(SETTLEMENT))
        self.assertEqual(len(parsed["split_payouts"]), 2)

    def test_accepts_already_parsed_dict(self):
        self.assertEqual(parse_settlement_payload(SETTLEMENT)["payout_id"], "PTTEST0001")

    def test_rejects_unparseable_payload(self):
        for bad in (None, "", "   ", "not a payload"):
            with self.assertRaises(SettlementError):
                parse_settlement_payload(bad)


class TestModeRules(unittest.TestCase):
    def test_rules_off_debits_every_mode(self):
        self.assertTrue(resolve_rule("Credit Card", None, "Debit", set()))

    def test_configured_mode_is_honoured(self):
        rules = {"UPI": True, "Credit Card": False}
        self.assertTrue(resolve_rule("UPI", rules, "Debit", set()))
        self.assertFalse(resolve_rule("Credit Card", rules, "Debit", set()))

    def test_matching_is_case_sensitive(self):
        """'credit card' is not 'Credit Card' -- it is an unrecognised mode."""
        unknown = set()
        resolve_rule("credit card", {"Credit Card": False}, "Debit", unknown)
        self.assertIn("credit card", unknown)

    def test_unknown_mode_behaviour(self):
        self.assertTrue(resolve_rule("Wallet", {}, "Debit", set()))
        self.assertFalse(resolve_rule("Wallet", {}, "Skip", set()))
        with self.assertRaises(SettlementError):
            resolve_rule("Wallet", {}, "Fail", set())


class TestSegregation(unittest.TestCase):
    """Needs Bank Accounts for the two account numbers above; skipped otherwise."""

    @classmethod
    def setUpClass(cls):
        import frappe

        cls.frappe = frappe
        cls.have_fixtures = all(
            frappe.db.exists("Bank Account", {"bank_account_no": number})
            for number in ("50200011443440", "50200080706351")
        )

    def setUp(self):
        if not self.have_fixtures:
            self.skipTest("Bank Accounts for the sample account numbers are not set up")

    def test_bank_totals_ignore_payment_mode_rules(self):
        """A mode rule must never remove money that physically reached the bank."""
        all_on = segregate(SETTLEMENT, None, "Debit")
        cards_off = segregate(SETTLEMENT, {"Netbanking": True, "Credit Card": False}, "Debit")
        self.assertEqual(
            {c: b["bank_total"] for c, b in all_on["companies"].items()},
            {c: b["bank_total"] for c, b in cards_off["companies"].items()},
        )

    def test_charges_split_by_mode(self):
        result = segregate(SETTLEMENT, {"Netbanking": True, "Credit Card": False}, "Debit")
        included = sum(b["included"] for b in result["companies"].values())
        skipped = sum(b["skipped"] for b in result["companies"].values())
        self.assertAlmostEqual(included, 9.44, places=2)
        self.assertAlmostEqual(skipped, 9.44, places=2)
        self.assertAlmostEqual(included + skipped, 18.88, places=2)

    def test_included_plus_skipped_reconciles_to_header(self):
        result = segregate(SETTLEMENT, {"Netbanking": True, "Credit Card": False}, "Debit")
        validate_segregation(SETTLEMENT, result, 0.50)

    def test_orphan_charge_fails_validation(self):
        """A charge whose split_payout_id has no bank split cannot be booked."""
        payload = json.loads(json.dumps(SETTLEMENT))
        payload["settled_transactions"][0]["split_transactions"][0]["split_payout_id"] = "SPZ"
        result = segregate(payload, None, "Debit")
        with self.assertRaises(SettlementError):
            validate_segregation(payload, result, 0.50)

    def test_payload_without_split_payouts_is_rejected(self):
        with self.assertRaises(SettlementError):
            segregate({"payout_id": "X", "split_payouts": []}, None, "Debit")
