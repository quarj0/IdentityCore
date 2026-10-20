from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.audit.services import record_audit_event
from apps.claims import disclosure, serializers, services
from apps.claims.models import ClaimEvidence, ClaimReusePolicy, ClaimSource
from apps.evidence.access import current_actor
from apps.evidence.services import _scope
from apps.evidence.views import GovernedAPIView
from common.pagination import paginate_cursor_results
from common.responses import success_response


class ClaimsAPIView(GovernedAPIView):
    read_permission = "claims:read"
    write_permission = "claims:write"


class ClaimListView(ClaimsAPIView):
    @transaction.atomic
    def get(self, request):
        data = self.parsed(serializers.ClaimQuery, request.query_params)
        tenant, project, _ = _scope(self.tenant(request).pk, data["project_id"])
        actor = current_actor(
            self.actor(request), tenant, "claims:read", project=project
        )
        now = timezone.now()
        query = services._select_related().filter(
            tenant=tenant,
            project=project,
            purpose=data["purpose"],
            status="active",
            deleted_at__isnull=True,
            valid_from__lte=now,
            valid_until__gt=now,
            delete_after__gt=now,
        )
        items, pagination = paginate_cursor_results(
            query,
            request,
            cursor_scope=f"claims:{tenant.public_id}:{project.public_id}:{actor.public_id}",
        )
        results = []
        for item in items:
            try:
                results.append(
                    services.read_claim(
                        tenant_id=tenant.pk,
                        actor=actor,
                        claim_id=item.public_id,
                        request=request,
                        **data,
                    )
                )
            except PermissionDenied:
                continue
        return success_response(
            {"results": results, "pagination": pagination}, request=request
        )

    def post(self, request):
        data = self.parsed(serializers.ClaimInput, request.data)

        def create():
            item = services.create_claim(
                tenant_id=self.tenant(request).pk,
                actor=self.actor(request),
                request=request,
                **data,
            )
            return {
                "id": item.public_id,
                "schema_id": item.schema.public_id,
                "created_at": item.created_at.isoformat(),
            }

        return self.write(request, "claims.create", create)


class ClaimDetailView(ClaimsAPIView):
    def get(self, request, claim_id):
        data = self.parsed(serializers.ClaimQuery, request.query_params)
        return success_response(
            services.read_claim(
                tenant_id=self.tenant(request).pk,
                actor=self.actor(request),
                claim_id=claim_id,
                request=request,
                **data,
            ),
            request=request,
        )


class ClaimLineageView(ClaimsAPIView):
    @transaction.atomic
    def get(self, request, claim_id):
        data = self.parsed(serializers.ClaimQuery, request.query_params)
        tenant, project, _ = _scope(self.tenant(request).pk, data["project_id"])
        actor = current_actor(
            self.actor(request), tenant, "claims:read", project=project
        )
        record = get_object_or_404(
            services._select_related(),
            tenant=tenant,
            project=project,
            purpose=data["purpose"],
            public_id=claim_id,
        )
        claims, evidence = services.claim_lineage(record)
        nodes = [
            {
                "id": item.public_id,
                "resource_type": "claim",
                "schema_id": item.schema.public_id,
                "status": item.status,
            }
            for item in sorted(claims.values(), key=lambda item: item.pk)
        ]
        nodes += [
            {
                "id": item.public_id,
                "resource_type": "evidence",
                "schema_id": item.schema.public_id,
                "status": item.status,
            }
            for item in sorted(evidence.values(), key=lambda item: item.pk)
        ]
        from apps.evidence.models import EvidenceSource

        edges = [
            {
                "resource_id": claims[edge.claim_id].public_id,
                "source_id": claims[edge.source_id].public_id,
            }
            for edge in ClaimSource.objects.filter(
                claim_id__in=claims, source_id__in=claims
            )
        ]
        edges += [
            {
                "resource_id": claims[edge.claim_id].public_id,
                "source_id": evidence[edge.evidence_id].public_id,
            }
            for edge in ClaimEvidence.objects.filter(
                claim_id__in=claims, evidence_id__in=evidence
            )
        ]
        edges += [
            {
                "resource_id": evidence[edge.evidence_id].public_id,
                "source_id": evidence[edge.source_id].public_id,
            }
            for edge in EvidenceSource.objects.filter(
                evidence_id__in=evidence, source_id__in=evidence
            )
        ]
        record_audit_event(
            tenant=tenant,
            actor=actor,
            action="claims.lineage_accessed",
            target_type="claim",
            target_id=record.public_id,
            request=request,
            metadata={"node_count": len(nodes)},
        )
        return success_response(
            {
                "root_id": record.public_id,
                "nodes": nodes,
                "edges": edges,
                "truncated": False,
            },
            request=request,
        )


class ClaimReviewView(ClaimsAPIView):
    write_permission = "claims:review"
    additional_write_operations = ("claims:write",)

    def post(self, request, claim_id):
        data = self.parsed(serializers.ReviewInput, request.data)

        def review():
            item = services.resolve_conflict(
                tenant_id=self.tenant(request).pk,
                actor=self.actor(request),
                claim_id=claim_id,
                request=request,
                **data,
            )
            return {
                "id": item.public_id,
                "outcome": item.outcome,
                "selected_claim_id": item.selected_claim.public_id
                if item.selected_claim_id
                else None,
            }

        return self.write(request, f"claims.review:{claim_id}", review, status=200)


class ClaimRevokeView(ClaimsAPIView):
    def post(self, request, claim_id):
        data = self.parsed(serializers.RevokeInput, request.data)

        def revoke():
            item = services.revoke_claim(
                tenant_id=self.tenant(request).pk,
                actor=self.actor(request),
                claim_id=claim_id,
                request=request,
                **data,
            )
            return {"id": item.public_id, "status": item.status}

        return self.write(request, f"claims.revoke:{claim_id}", revoke, status=200)


class ClaimEvaluateView(ClaimsAPIView):
    write_permission = "claims:read"

    def post(self, request, claim_id):
        data = self.parsed(serializers.EvaluationInput, request.data)
        return success_response(
            disclosure.evaluate_claim(
                tenant_id=self.tenant(request).pk,
                actor=self.actor(request),
                claim_id=claim_id,
                request=request,
                **data,
            ),
            request=request,
        )


class PolicyListView(ClaimsAPIView):
    @transaction.atomic
    def get(self, request):
        data = self.parsed(serializers.ProjectQuery, request.query_params)
        tenant, project, _ = _scope(self.tenant(request).pk, data["project_id"])
        current_actor(self.actor(request), tenant, "claims:read", project=project)
        items, pagination = paginate_cursor_results(
            ClaimReusePolicy.objects.select_related("project", "schema").filter(
                tenant=tenant, project=project, retired_at__isnull=True
            ),
            request,
            cursor_scope=f"claim-policies:{tenant.public_id}:{project.public_id}",
        )
        return success_response(
            {
                "results": [serializers.policy_summary(item) for item in items],
                "pagination": pagination,
            },
            request=request,
        )

    def post(self, request):
        data = self.parsed(serializers.PolicyInput, request.data)
        return self.write(
            request,
            "claims.policy.create",
            lambda: serializers.policy_summary(
                disclosure.propose_policy(
                    tenant_id=self.tenant(request).pk,
                    actor=self.actor(request),
                    request=request,
                    **data,
                )
            ),
        )


class PolicyApproveView(ClaimsAPIView):
    write_permission = "authorizations:approve"
    additional_write_operations = ("claims:read",)

    def post(self, request, policy_id):
        data = self.parsed(serializers.ProjectInput, request.data)
        return self.write(
            request,
            f"claims.policy.approve:{policy_id}",
            lambda: serializers.policy_summary(
                disclosure.approve_policy(
                    tenant_id=self.tenant(request).pk,
                    actor=self.actor(request),
                    policy_id=policy_id,
                    request=request,
                    **data,
                )
            ),
            status=200,
        )


class DisclosureIssueView(ClaimsAPIView):
    write_permission = "claims:disclose"

    def post(self, request):
        data = self.parsed(serializers.DisclosureInput, request.data)
        ephemeral = []

        def issue():
            item, token = disclosure.issue_disclosure(
                tenant_id=self.tenant(request).pk,
                actor=self.actor(request),
                request=request,
                **data,
            )
            ephemeral.append(token)
            # Only this receipt is persisted in shared idempotency storage.
            return {
                "id": item.public_id,
                "audience_id": item.audience.public_id,
                "purpose": item.purpose,
                "expires_at": item.expires_at.isoformat(),
                "max_redemptions": item.max_redemptions,
            }

        response = self.write(request, "claims.disclosure.issue", issue)
        response.data["data"] = {
            **response.data["data"],
            "token": ephemeral[0] if ephemeral else None,
            "token_available": bool(ephemeral),
        }
        return response


class DisclosureRedeemView(ClaimsAPIView):
    write_permission = "claims:read"

    def post(self, request, disclosure_id):
        data = self.parsed(serializers.ProjectInput, request.data)
        payload = disclosure.redeem_disclosure(
            tenant_id=self.tenant(request).pk,
            actor=self.actor(request),
            disclosure_id=disclosure_id,
            token=request.headers.get("X-Disclosure-Token", ""),
            request_key=request.headers.get("Idempotency-Key", ""),
            request=request,
            **data,
        )
        return success_response(payload, request=request)


class DisclosureRevokeView(ClaimsAPIView):
    write_permission = "claims:disclose"

    def post(self, request, disclosure_id):
        data = self.parsed(serializers.ProjectInput, request.data)

        def revoke():
            item = disclosure.revoke_disclosure(
                tenant_id=self.tenant(request).pk,
                actor=self.actor(request),
                disclosure_id=disclosure_id,
                request=request,
                **data,
            )
            return {"id": item.public_id, "revoked": item.revoked_at is not None}

        return self.write(
            request, f"claims.disclosure.revoke:{disclosure_id}", revoke, status=200
        )


class PolicyRetireView(ClaimsAPIView):
    write_permission = "authorizations:write"
    allow_inactive_write_context = True

    def post(self, request, policy_id):
        data = self.parsed(serializers.ProjectInput, request.data)
        return self.write(
            request,
            f"claims.policy.retire:{policy_id}",
            lambda: serializers.policy_summary(
                disclosure.retire_policy(
                    tenant_id=self.tenant(request).pk,
                    actor=self.actor(request),
                    policy_id=policy_id,
                    request=request,
                    **data,
                )
            ),
            status=200,
        )
