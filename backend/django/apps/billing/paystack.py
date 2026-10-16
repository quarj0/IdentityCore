"""Paystack payment adapter. Server secret never leaves this module.

Business logic uses gateway reference, amount in minor units and currency;
other gateways can implement initialize() and verify() with same result shape.
"""

import hashlib
import hmac
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from django.conf import settings
from apps.billing.exceptions import GatewayError
from apps.billing.gateways import checked_checkout_url, payment_return_url

BASE = "https://api.paystack.co"
MAX_RESPONSE = 65536
REFERENCE = re.compile(r"[-.=_A-Za-z0-9]{1,64}\Z")
SIGNATURE = re.compile(r"[a-fA-F0-9]{128}\Z")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GatewayError("Gateway redirect refused")


def _secret():
    value = getattr(settings, "PAYSTACK_SECRET_KEY", "")
    if not value:
        raise GatewayError("Payment gateway is not configured")
    return value


def _api(method, path, *, payload=None, list_response=False):
    if (
        not path.startswith("/")
        or "?" in path
        and not path.startswith(("/transaction/verify/", "/refund?"))
    ):
        raise GatewayError("Invalid gateway endpoint")
    body = (
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
        if payload is not None
        else None
    )
    req = urllib.request.Request(
        BASE + path,
        data=body,
        method=method,
        headers={
            "Authorization": "Bearer " + _secret(),
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "IdentityCore/1.0",
        },
    )
    try:
        with urllib.request.build_opener(_NoRedirect).open(req, timeout=8) as response:
            data = response.read(MAX_RESPONSE + 1)
            if response.status != 200 or len(data) > MAX_RESPONSE:
                raise GatewayError("Gateway returned an invalid response")
    except (OSError, ValueError, urllib.error.HTTPError) as exc:
        raise GatewayError("Gateway is temporarily unavailable") from exc
    try:
        result = json.loads(data)
    except (ValueError, UnicodeDecodeError) as exc:
        raise GatewayError("Gateway returned malformed JSON") from exc
    if (
        not isinstance(result, dict)
        or result.get("status") is not True
        or not isinstance(result.get("data"), list if list_response else dict)
    ):
        raise GatewayError("Gateway rejected the request")
    return result["data"]


def initialize(*, reference, email, amount_minor, currency, payment_id=""):
    if not REFERENCE.fullmatch(reference) or not 1 <= amount_minor < 10**14:
        raise GatewayError("Invalid payment parameters")
    if currency != "GHS":
        raise GatewayError("Configured Paystack merchant supports GHS only")
    if not isinstance(email, str) or "@" not in email:
        raise GatewayError("Invalid billing email")
    callback_url = payment_return_url(payment_id)
    data = _api(
        "POST",
        "/transaction/initialize",
        payload={
            "email": email,
            "amount": str(amount_minor),
            "currency": currency,
            "reference": reference,
            "callback_url": callback_url,
        },
    )
    url = data.get("authorization_url")
    if data.get("reference") != reference:
        raise GatewayError("Gateway checkout verification failed")
    return checked_checkout_url(url, "paystack")


def verify(*, reference):
    if not REFERENCE.fullmatch(reference):
        raise GatewayError("Invalid payment reference")
    return _api("GET", "/transaction/verify/" + urllib.parse.quote(reference, safe=""))


def valid_webhook(body, signature):
    if not isinstance(signature, str) or not SIGNATURE.fullmatch(signature):
        return False
    if not isinstance(body, bytes) or not 0 < len(body) <= 65536:
        return False
    computed = hmac.new(_secret().encode("utf-8"), body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(computed, signature.lower())


def verify_refund(*, refund_id):
    """Independently fetch the refund before recording any credit adjustment."""
    if type(refund_id) is not int or refund_id <= 0:
        raise GatewayError("Invalid refund identifier")
    return _api("GET", "/refund/" + str(refund_id))


def verify_dispute(*, dispute_id):
    if type(dispute_id) is not int or dispute_id <= 0:
        raise GatewayError("Invalid dispute identifier")
    return _api("GET", "/dispute/" + str(dispute_id))


def list_refunds(*, transaction_id):
    """Read authenticated refund facts for one already settled transaction."""
    if type(transaction_id) is not int or transaction_id <= 0:
        raise GatewayError("Invalid refund transaction identifier")
    refunds = []
    for page in range(1, 21):
        query = urllib.parse.urlencode(
            {
                "transaction": transaction_id,
                "perPage": 50,
                "page": page,
            }
        )
        rows = _api("GET", "/refund?" + query, list_response=True)
        if not isinstance(rows, list) or len(rows) > 50:
            raise GatewayError("Invalid refund listing")
        refunds.extend(rows)
        if len(rows) < 50:
            return refunds
    raise GatewayError("Refund history exceeds automatic reconciliation bounds")
