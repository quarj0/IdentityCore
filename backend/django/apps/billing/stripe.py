"""Stripe Checkout with exact invoice amounts and authenticated reconciliation.

API contract: https://docs.stripe.com/api/checkout/sessions/create
Webhook contract: https://docs.stripe.com/webhooks/signature
The local reference is both the idempotency key and the server-owned correlation ID.
"""

import hashlib
import hmac
import json
import re
import time
from urllib import error, parse, request

from django.conf import settings

from apps.billing.exceptions import GatewayError
from apps.billing.gateways import checked_checkout_url, payment_return_url

API_BASE = "https://api.stripe.com/v1"
API_VERSION = "2025-06-30.basil"
MAX_RESPONSE = 65536
IDENTIFIER = re.compile(r"(?:cs_(?:test_|live_)?|pi_|re_|dp_|evt_)[A-Za-z0-9]{1,100}\Z")
REFERENCE = re.compile(r"[-.=_A-Za-z0-9]{1,64}\Z")


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GatewayError("Gateway redirect refused")


def _api(method, path, *, payload=None, idempotency_key=None):
    secret = getattr(settings, "STRIPE_SECRET_KEY", "")
    if not secret:
        raise GatewayError("Stripe is not configured")
    body = parse.urlencode(payload).encode() if payload is not None else None
    headers = {
        "Authorization": "Bearer " + secret,
        "Stripe-Version": API_VERSION,
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    req = request.Request(API_BASE + path, data=body, method=method, headers=headers)
    try:
        with request.build_opener(_NoRedirect).open(req, timeout=8) as response:
            data = response.read(MAX_RESPONSE + 1)
            if response.status != 200 or len(data) > MAX_RESPONSE:
                raise GatewayError("Stripe returned an invalid response")
    except (OSError, ValueError, error.HTTPError) as exc:
        raise GatewayError("Stripe is temporarily unavailable") from exc
    try:
        result = json.loads(data)
    except (ValueError, UnicodeDecodeError) as exc:
        raise GatewayError("Stripe returned malformed JSON") from exc
    if not isinstance(result, dict) or "error" in result:
        raise GatewayError("Stripe rejected the request")
    return result


def _identifier(value, prefix):
    if (
        not isinstance(value, str)
        or not value.startswith(prefix)
        or not IDENTIFIER.fullmatch(value)
    ):
        raise GatewayError("Invalid Stripe resource identifier")
    return value


def initialize(*, reference, email, amount_minor, currency, payment_id=""):
    if (
        not isinstance(reference, str)
        or not REFERENCE.fullmatch(reference)
        or type(amount_minor) is not int
        or not 1 <= amount_minor <= 99999999
        or currency
        not in getattr(settings, "STRIPE_PAYMENT_CURRENCIES", ("USD", "EUR", "GBP"))
        or not isinstance(email, str)
        or "@" not in email
    ):
        raise GatewayError("Invalid Stripe checkout parameters")
    return_url = payment_return_url(payment_id)
    result = _api(
        "POST",
        "/checkout/sessions",
        idempotency_key=reference,
        payload={
            "mode": "payment",
            "client_reference_id": reference,
            "customer_email": email,
            "success_url": return_url,
            "cancel_url": return_url,
            "metadata[identitycore_payment_reference]": reference,
            "payment_intent_data[metadata][identitycore_payment_reference]": reference,
            "line_items[0][quantity]": 1,
            "line_items[0][price_data][currency]": currency.lower(),
            "line_items[0][price_data][unit_amount]": amount_minor,
            "line_items[0][price_data][product_data][name]": "IdentityCore invoice",
        },
    )
    session_id = _identifier(result.get("id"), "cs_")
    url = result.get("url")
    checked_checkout_url(url, "stripe")
    if (
        result.get("client_reference_id") != reference
        or result.get("mode") != "payment"
        or type(result.get("amount_total")) is not int
        or result["amount_total"] != amount_minor
        or result.get("currency") != currency.lower()
    ):
        raise GatewayError("Stripe checkout attribution failed")
    return {"id": session_id, "url": url}


def verify(*, reference, checkout_id):
    session_id = _identifier(checkout_id, "cs_")
    result = _api("GET", "/checkout/sessions/" + session_id)
    if (
        result.get("id") != session_id
        or result.get("client_reference_id") != reference
        or result.get("mode") != "payment"
    ):
        raise GatewayError("Stripe session attribution failed")
    amount = result.get("amount_total")
    currency = result.get("currency")
    if type(amount) is not int or not isinstance(currency, str):
        raise GatewayError("Stripe session amount is missing")
    normalized = {
        "reference": reference,
        "amount": amount,
        "currency": currency.upper(),
        "status": "pending",
        "id": None,
        "checkout_id": session_id,
    }
    if result.get("status") == "expired":
        normalized["status"] = "failed"
        return normalized
    intent_id = result.get("payment_intent")
    if not intent_id:
        return normalized
    intent_id = _identifier(intent_id, "pi_")
    intent = _api("GET", "/payment_intents/" + intent_id)
    metadata = intent.get("metadata")
    if (
        intent.get("id") != intent_id
        or intent.get("amount") != amount
        or type(intent.get("amount")) is not int
        or intent.get("currency") != currency
        or not isinstance(metadata, dict)
        or metadata.get("identitycore_payment_reference") != reference
    ):
        raise GatewayError("Stripe payment attribution failed")
    if result.get("status") != "open" and intent.get("status") in (
        "canceled",
        "requires_payment_method",
    ):
        normalized["status"] = "failed"
    elif (
        intent.get("status") == "succeeded"
        and result.get("status") == "complete"
        and result.get("payment_status") == "paid"
        and type(intent.get("amount_received")) is int
        and intent["amount_received"] == amount
    ):
        normalized.update(status="success", id=intent_id)
    return normalized


def valid_webhook(body, signature, *, now=None):
    secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise GatewayError("Stripe webhook signing secret is not configured")
    if (
        not isinstance(body, bytes)
        or not 0 < len(body) <= MAX_RESPONSE
        or not isinstance(signature, str)
        or len(signature) > 2048
    ):
        return False
    pairs = [part.strip().split("=", 1) for part in signature.split(",")]
    timestamps = [p[1] for p in pairs if len(p) == 2 and p[0] == "t"]
    signatures = [
        p[1]
        for p in pairs
        if len(p) == 2 and p[0] == "v1" and re.fullmatch(r"[a-fA-F0-9]{64}", p[1])
    ]
    if len(timestamps) != 1 or not re.fullmatch(r"[0-9]{1,12}", timestamps[0]):
        return False
    timestamp = int(timestamps[0])
    if abs((time.time() if now is None else now) - timestamp) > 300:
        return False
    digest = hmac.new(
        secret.encode(), timestamps[0].encode() + b"." + body, hashlib.sha256
    ).hexdigest()
    return any(hmac.compare_digest(digest, value.lower()) for value in signatures)


def verify_refund(*, refund_id):
    return _api("GET", "/refunds/" + _identifier(refund_id, "re_"))


def verify_dispute(*, dispute_id):
    return _api("GET", "/disputes/" + _identifier(dispute_id, "dp_"))
