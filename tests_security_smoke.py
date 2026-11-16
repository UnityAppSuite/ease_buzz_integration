from hashlib import sha512
from unittest.mock import patch

import requests

from easebuzz.easebuzz.utils import payment
from easebuzz.easebuzz.utils.http import post_with_retries


def build_callback_payload(salt="secret"):
    data = {
        "status": "success",
        "txnid": "txn-1",
        "amount": "100.00",
        "productinfo": "Order",
        "firstname": "Test",
        "email": "test@example.com",
        "phone": "9999999999",
        "udf1": "Payment Request",
        "udf2": "PR-0001",
        "udf3": "",
        "udf4": "",
        "udf5": "",
        "key": "merchant",
        "surl": "https://example.com/success",
        "furl": "https://example.com/failure",
    }
    seq = "udf10|udf9|udf8|udf7|udf6|udf5|udf4|udf3|udf2|udf1|email|firstname|productinfo|amount|txnid|key".split("|")
    reverse = salt + "|" + data["status"]
    for field in seq:
        reverse += "|" + str(data.get(field, ""))
    data["hash"] = sha512(reverse.encode("utf-8")).hexdigest().lower()
    return data


payload = build_callback_payload()
assert payment.easebuzzResponse(payload, "secret")["status"] == 1

with patch("easebuzz.easebuzz.utils.http.requests.post") as mocked:
    mocked.side_effect = [
        requests.Timeout(),
        type("Resp", (), {"status_code": 200, "content": b"{}"})(),
    ]
    response = post_with_retries("https://example.com", {"a": 1}, max_attempts=2, backoff_seconds=0)
    assert response.status_code == 200

print("security smoke checks passed")
