"""Audit same-tenant environment denials without disclosing object existence."""

from django.http import Http404
from rest_framework.exceptions import NotFound

from apps.audit.services import record_audit_event


class EnvironmentDenialAuditMixin:
    def _remember_environment_lookup(self, request, original, scoped):
        identifier = self.kwargs.get("verification_id") or self.kwargs.get("policy_id")
        if identifier and getattr(request, "api_client", None) is not None:
            self._environment_denial_probe = (
                original.filter(tenant=self._get_tenant(request), public_id=identifier),
                scoped.filter(tenant=self._get_tenant(request), public_id=identifier),
                identifier,
            )
        return scoped

    def handle_exception(self, exc):
        # APIView handles errors after a method's atomic decorator has unwound.
        # Persist this event outside the rejected mutation's rollback.
        probe = getattr(self, "_environment_denial_probe", None)
        if isinstance(exc, (Http404, NotFound)) and probe is not None:
            original, scoped, identifier = probe
            if original.exists() and not scoped.exists():
                record_audit_event(
                    tenant=self._get_tenant(self.request),
                    actor=self.request.api_client,
                    request=self.request,
                    action="environment_scope.denied",
                    target_type=self.environment_audit_target,
                    target_id=identifier,
                    metadata={
                        "reason": "environment_mismatch",
                        "method": self.request.method,
                    },
                )
        return super().handle_exception(exc)
