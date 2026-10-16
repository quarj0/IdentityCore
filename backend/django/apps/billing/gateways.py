from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings

from apps.billing.exceptions import GatewayError


def gateway_for(provider):
    from apps.billing import paystack, stripe

    adapters = {"paystack": paystack, "stripe": stripe}
    if provider not in adapters:
        raise GatewayError("Unsupported payment provider")
    return adapters[provider]


def enabled_providers(currency=None):
    if getattr(settings, "BILLING_PAYMENTS_ENABLED", False) is not True:
        return []
    configured = getattr(settings, "BILLING_PAYMENT_PROVIDERS", ("paystack",))
    currencies = getattr(settings, "STRIPE_PAYMENT_CURRENCIES", ("USD", "EUR", "GBP"))
    return [
        provider
        for provider in ("paystack", "stripe")
        if provider in configured
        and (
            currency is None
            or (provider == "paystack" and currency == "GHS")
            or (provider == "stripe" and currency in currencies)
        )
    ]


def payment_return_url(payment_id):
    value = getattr(settings, "BILLING_RETURN_URL", "")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise GatewayError("Secure payment return URL is not configured")
    query = [
        (key, item) for key, item in parse_qsl(parsed.query) if key != "payment_id"
    ]
    if payment_id:
        query.append(("payment_id", payment_id))
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), ""))


def checked_checkout_url(value, provider):
    hosts = {"paystack": "checkout.paystack.com", "stripe": "checkout.stripe.com"}
    try:
        parsed = urlsplit(value) if isinstance(value, str) else None
        valid = (
            parsed is not None
            and 0 < len(value) <= 2048
            and parsed.scheme == "https"
            and parsed.hostname == hosts.get(provider)
            and not parsed.username
            and not parsed.password
            and parsed.port in (None, 443)
        )
    except ValueError:
        valid = False
    if not valid:
        raise GatewayError("Gateway checkout URL is invalid")
    return value
