"""Opt-in safety checks for Easebuzz Fees callbacks.

Both checks are switched on/off from the BIS Fees Settings single doctype
(registered as "Fees Settings" on sites that have it) and default to off.
"""

import hmac
from hashlib import sha512

import frappe

SETTINGS_DOCTYPE = "Fees Settings"

# Same order as easebuzz.easebuzz.utils.payment._getReverseHashKey
_REVERSE_HASH_FIELDS = (
	"udf10",
	"udf9",
	"udf8",
	"udf7",
	"udf6",
	"udf5",
	"udf4",
	"udf3",
	"udf2",
	"udf1",
	"email",
	"firstname",
	"productinfo",
	"amount",
	"txnid",
	"key",
)


def switch(fieldname: str) -> bool:
	"""Read a Check field from Fees Settings; False if doctype/field is missing or on any error."""
	try:
		return bool(int(frappe.db.get_single_value(SETTINGS_DOCTYPE, fieldname) or 0))
	except Exception:
		return False


def all_salts() -> list[str]:
	"""Salts of every Easebuzz Settings document (e.g. surcharge 0 and 1)."""
	salts = []
	for name in frappe.get_all("Easebuzz Settings", pluck="name"):
		salt = frappe.get_doc("Easebuzz Settings", name).get_password("salt", raise_exception=False)
		if salt and salt not in salts:
			salts.append(salt)
	return salts


def _text(value) -> str:
	return "" if value is None else str(value)


def _reverse_hash(data, salt: str) -> str:
	parts = [salt, _text(data.get("status"))]
	parts.extend(_text(data.get(field)) for field in _REVERSE_HASH_FIELDS)
	hash_string = "|".join(parts)

	# NOT VERIFIED against a live callback: taken from Easebuzz's documented
	# sequence, which prefixes "additional_charges|" when the response carries
	# an additional_charges parameter.
	if data.get("additional_charges") is not None:
		hash_string = f"{_text(data.get('additional_charges'))}|{hash_string}"

	return sha512(hash_string.encode("utf-8")).hexdigest().lower()


def signature_valid(data, salts) -> bool:
	"""True if data["hash"] equals the Easebuzz reverse hash for any of `salts`."""
	received = _text(data.get("hash")).strip().lower()
	if not received or not salts:
		return False

	received = received.encode("utf-8")
	valid = False
	for salt in salts:
		if hmac.compare_digest(_reverse_hash(data, salt).encode("utf-8"), received):
			valid = True
	return valid
