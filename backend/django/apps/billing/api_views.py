"""Tenant-scoped, internal billing control plane and signed gateway callback."""

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.audit.services import record_audit_event
from apps.accounts.models import PlatformUser
from apps.billing import paystack
from apps.billing.exceptions import GatewayError
from apps.billing.gateways import enabled_providers
from apps.billing.models import (
    BillingInvoice,
    BillingPayment,
    BillingPlan,
    BillingSubscription,
)
from apps.billing.services import (
    BillingError,
    begin_checkout,
    confirm_gateway_payment,
    receive_paystack_webhook,
)
from common.permissions import IsTenantUser
from common.authorization import AuthorizationAction, decide_user_access
from common.responses import error_response, success_response


class IsBillingTenantUser(IsTenantUser):
    """Payment administration is never available to machine API credentials."""

    def has_permission(self, request, view):
        return (
            isinstance(request.user, PlatformUser)
            and request.user.is_active
            and super().has_permission(request, view)
        )


def serialize_invoice(invoice, *, include_lines=False, request=None):
    can_manage = bool(
        request
        and decide_user_access(
            request.user,
            action=AuthorizationAction.TENANT_ACCESS,
            permission_code="manage_billing",
        ).allowed
    )
    result = {
        "id": invoice.public_id,
        "currency": invoice.currency,
        "period_start": invoice.period_start.isoformat(),
        "period_end": invoice.period_end.isoformat(),
        "plan_code": invoice.plan_code,
        "plan_version": invoice.plan_version,
        "amount_minor": invoice.amount_minor,
        "status": invoice.status,
        "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
        "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
        "due_at": invoice.due_at.isoformat() if invoice.due_at else None,
        "payment_providers": enabled_providers(invoice.currency) if can_manage else [],
        "can_manage_billing": can_manage,
    }
    payment = invoice.payments.order_by("-created_at").first()
    result["payment"] = (
        {
            "id": payment.public_id,
            "provider": payment.provider,
            "status": payment.status,
        }
        if payment is not None
        else None
    )
    if include_lines:
        result["lines"] = [
            {
                "description": line.description,
                "quantity": line.quantity,
                "unit_price_minor": line.unit_price_minor,
                "amount_minor": line.amount_minor,
            }
            for line in invoice.lines.order_by("id")
        ]
    return result


class BillingPlansView(APIView):
    permission_classes = [IsAuthenticated, IsBillingTenantUser]

    def get(self, request):
        plans = BillingPlan.objects.filter(
            published=True, deleted_at__isnull=True
        ).order_by("name")
        return success_response(
            {
                "results": [
                    {
                        "id": plan.public_id,
                        "code": plan.code,
                        "version": plan.version,
                        "name": plan.name,
                        "currency": plan.currency,
                        "monthly_price_minor": plan.monthly_price_minor,
                        "meters": [
                            {
                                "provider_scope": m.provider_scope,
                                "capability": m.capability,
                                "outcome": m.outcome,
                                "unit_price_minor": m.unit_price_minor,
                            }
                            for m in plan.meters.order_by("id")
                        ],
                    }
                    for plan in plans
                ]
            },
            request=request,
        )


class BillingAccountView(APIView):
    permission_classes = [IsAuthenticated, IsBillingTenantUser]

    def get(self, request):
        subscription = (
            BillingSubscription.objects.filter(tenant=request.user.tenant)
            .select_related("plan")
            .first()
        )
        return success_response(
            {
                "subscription": (
                    {
                        "id": subscription.public_id,
                        "plan": subscription.plan.code,
                        "currency": subscription.plan.currency,
                        "status": subscription.status,
                        "started_at": subscription.started_at.isoformat(),
                    }
                    if subscription
                    else None
                )
            },
            request=request,
        )


class BillingSubscribeView(APIView):
    permission_classes = [IsAuthenticated, IsBillingTenantUser]
    required_permission_code = "manage_billing"

    def post(self, request):
        if not isinstance(request.data, dict) or set(request.data) != {"plan_id"}:
            return error_response(
                "invalid_plan", "Choose a published plan.", request=request
            )
        plan = get_object_or_404(
            BillingPlan,
            public_id=request.data["plan_id"],
            published=True,
            deleted_at__isnull=True,
        )
        if (
            request.user.tenant.status != "active"
            or request.user.tenant.organization.status != "active"
        ):
            return error_response(
                "organization_not_approved",
                "Active organization approval is required.",
                request=request,
                status=403,
            )
        from django.utils import timezone

        try:
            with transaction.atomic():
                sub = BillingSubscription.objects.create(
                    tenant=request.user.tenant,
                    plan=plan,
                    started_at=timezone.now(),
                    status="active",
                )
                record_audit_event(
                    tenant=request.user.tenant,
                    actor=request.user,
                    action="billing.subscription.created",
                    target_type="billing_subscription",
                    target_id=sub.public_id,
                    metadata={"plan_code": plan.code, "plan_version": plan.version},
                )
        except IntegrityError:
            return error_response(
                "subscription_exists",
                "Contact support to change an existing plan.",
                request=request,
                status=409,
            )
        return success_response(
            {
                "id": sub.public_id,
                "plan": plan.code,
                "status": sub.status,
            },
            request=request,
            status=201,
        )


class BillingInvoiceListView(APIView):
    permission_classes = [IsAuthenticated, IsBillingTenantUser]

    def get(self, request):
        items = BillingInvoice.objects.filter(tenant=request.user.tenant).order_by(
            "-period_start"
        )[:50]
        return success_response(
            {"results": [serialize_invoice(x, request=request) for x in items]},
            request=request,
        )


class BillingInvoiceDetailView(APIView):
    permission_classes = [IsAuthenticated, IsBillingTenantUser]

    def get(self, request, invoice_id):
        invoice = get_object_or_404(
            BillingInvoice, tenant=request.user.tenant, public_id=invoice_id
        )
        return success_response(
            serialize_invoice(invoice, include_lines=True, request=request),
            request=request,
        )


class BillingCheckoutView(APIView):
    permission_classes = [IsAuthenticated, IsBillingTenantUser]
    required_permission_code = "manage_billing"

    def post(self, request, invoice_id):
        invoice = get_object_or_404(
            BillingInvoice, tenant=request.user.tenant, public_id=invoice_id
        )
        if (
            not isinstance(request.data, dict)
            or set(request.data) - {"provider"}
            or (
                "provider" in request.data
                and request.data["provider"] not in ("paystack",)
            )
        ):
            return error_response(
                "invalid_checkout",
                "Invalid Paystack checkout request.",
                request=request,
            )
        try:
            payment = begin_checkout(
                invoice,
                billing_email=request.user.email,
                provider=request.data.get("provider"),
            )
        except BillingError as exc:
            return error_response(
                "checkout_unavailable", str(exc), request=request, status=409
            )
        except GatewayError:
            return error_response(
                "gateway_unavailable",
                "Payment gateway unavailable.",
                request=request,
                status=503,
            )
        record_audit_event(
            tenant=request.user.tenant,
            actor=request.user,
            action="billing.checkout.requested",
            target_type="billing_payment",
            target_id=payment.public_id,
        )
        return success_response(
            {
                "payment_id": payment.public_id,
                "reference": payment.reference,
                "amount_minor": payment.amount_minor,
                "currency": payment.currency,
                "checkout_url": payment.checkout_url,
                "provider": payment.provider,
                "status": payment.status,
            },
            request=request,
        )


class BillingPaymentStatusView(APIView):
    permission_classes = [IsAuthenticated, IsBillingTenantUser]

    def get(self, request, payment_id):
        payment = get_object_or_404(
            BillingPayment.objects.select_related("invoice"),
            public_id=payment_id,
            invoice__tenant=request.user.tenant,
        )
        return success_response(
            {
                "id": payment.public_id,
                "status": payment.status,
                "invoice_id": payment.invoice.public_id,
            },
            request=request,
        )

    def post(self, request, payment_id):
        if not IsBillingTenantUser().has_permission(
            request, type("_", (), {"required_permission_code": "manage_billing"})()
        ):
            return error_response(
                "permission_denied",
                "Billing permission required.",
                request=request,
                status=403,
            )
        payment = get_object_or_404(
            BillingPayment.objects.select_related("invoice"),
            public_id=payment_id,
            invoice__tenant=request.user.tenant,
        )
        try:
            confirmed = confirm_gateway_payment(payment.reference)
        except GatewayError:
            return error_response(
                "gateway_unavailable",
                "Payment verification unavailable.",
                request=request,
                status=503,
            )
        except BillingError:
            return error_response(
                "verification_mismatch",
                "Payment requires manual reconciliation.",
                request=request,
                status=409,
            )
        return success_response({"verified": confirmed}, request=request)


class PaystackWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def post(self, request):
        body = request.body
        if not body or len(body) > 65536:
            return HttpResponse(status=413)
        signature = request.headers.get("X-Paystack-Signature", "")
        try:
            receive_paystack_webhook(body, signature)
        except paystack.GatewayError:
            return HttpResponse(status=503)
        except BillingError:
            return HttpResponse(status=400)
        return HttpResponse(status=200)
