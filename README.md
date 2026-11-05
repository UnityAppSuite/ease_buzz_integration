## Easebuzz

EaseBuzz Integration

#### License

MIT
## BIS payment safety

Two opt-in safety checks for Easebuzz **Fees** callbacks (`EasebuzzSettings.handle_response`, reached from `easebuzz.api.webhook_handler` and `/easebuzz/success`). Both are Check fields in **BIS Fees Settings** (the `Fees Settings` single doctype from the BIS app) and **both default to off**; with both off, behaviour is unchanged. If that doctype or field does not exist on a site, the switch reads as off.

- `bis_verify_gateway_signature` – the callback's `hash` is checked against Easebuzz's reverse hash (`salt|status|udf10..udf1|email|firstname|productinfo|amount|txnid|key`, sha512), using the salt of any Easebuzz Settings document. A missing, empty or wrong hash is logged in Error Log (txnid, udf1-3 and status only, never the hash or salt), the callback returns `Invalid signature`, and the payment is not applied. The check runs before the Administrator login.
- `bis_rollback_failed_payments` – if processing a callback raises, `frappe.db.rollback()` is called before the error is logged, so nothing from the failed payment is committed.

Code: `easebuzz/easebuzz/utils/payment_safety.py`; tests: `easebuzz/easebuzz/utils/test_payment_safety.py`.

Fee checkout needs one valid student email address or an explicit payer email. A missing or invalid address now returns a clear error before contacting Easebuzz. This does not supply a default recipient or change the gateway environment.

### Not verified

- No live Easebuzz callback has been tested; the tests build hashes with the documented sequence and a made-up salt.
- When a response carries `additional_charges`, the hash string is prefixed with `additional_charges|`. That rule comes from Easebuzz's documented sequence and has **not** been checked against a real callback. Turn the signature switch on for a school only after confirming real callbacks (including ones with additional charges) pass.
- Web-form callbacks (`handle_response_web_form`, `udf3 == "webform"`) are untouched by both switches.
