from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from apps.api_clients.idempotency import (
    begin_idempotent_request,
    complete_idempotent_request,
)
from apps.audit.services import lock_audit_chain, record_audit_event
from apps.consent.services import ConsentProofUnavailable
from apps.evidence.access import current_actor
from apps.evidence.models import (
    Evidence,
    EvidenceSource,
    PurposeAuthorization,
    ResourceSchema,
)
from apps.evidence.serializers import (
    AuthorizationInput,
    EvidenceInput,
    ResourceQuery,
    RevokeInput,
    SchemaInput,
    authorization_summary,
    schema_summary,
)
from apps.evidence.services import (
    _scope,
    approve_authorization,
    create_evidence,
    create_schema,
    propose_authorization,
    read_evidence,
    revoke_authorization,
    revoke_evidence,
    ancestry,
)
from common.authentication import APIClientAuthentication
from common.pagination import paginate_cursor_results
from common.responses import success_response


class PurposeProofUnavailable(APIException):
    status_code = 503
    default_detail = "Purpose authorization is temporarily unavailable."
    default_code = "purpose_proof_unavailable"


class GovernedAPIView(APIView):
    authentication_classes = [
        APIClientAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]
    permission_classes = [IsAuthenticated]
    write_permission = None
    read_permission = "evidence:read"
    additional_write_operations = ()
    allow_inactive_write_context = False

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        from apps.tenants.models import Tenant

        tenant = Tenant.objects.get(pk=self.tenant(request).pk)
        operation = (
            self.read_permission
            if request.method in {"GET", "HEAD", "OPTIONS"}
            else self.write_permission or "evidence:write"
        )
        if (
            isinstance(self, (SchemaListView, SchemaDetailView))
            and request.method in {"GET", "HEAD", "OPTIONS"}
            and request.query_params.get("kind") == "claim"
        ):
            operation = "claims:read"
        current_actor(self.actor(request), tenant, operation)
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            for extra in self.additional_write_operations:
                current_actor(self.actor(request), tenant, extra)

    def finalize_response(self, request, response, *args, **kwargs):
        from django.utils.cache import patch_vary_headers

        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        response["Pragma"] = "no-cache"
        patch_vary_headers(response, ["Authorization", "X-Client-Id"])
        return response

    def actor(self, request):
        return getattr(request, "api_client", None) or request.user

    def tenant(self, request):
        actor = self.actor(request)
        if getattr(actor, "tenant_id", None) is None:
            raise PermissionDenied("A tenant-scoped actor is required.")
        return actor.tenant

    def parsed(self, serializer, data):
        parsed = serializer(data=data)
        parsed.is_valid(raise_exception=True)
        return parsed.validated_data

    @transaction.atomic
    def write(self, request, operation, callback, *, status=201):
        tenant = self.tenant(request)
        lock_audit_chain(tenant.pk)
        project_id = request.data.get("project_id") or request.query_params.get(
            "project_id"
        )
        tenant, project, _ = _scope(
            tenant.pk,
            project_id,
            allow_inactive_project=self.allow_inactive_write_context,
        )
        if operation == "evidence.schema.create":
            permission_operation = "schemas:write"
        elif operation.startswith("purpose.approve:"):
            permission_operation = "authorizations:approve"
        elif (
            operation.startswith("purpose.")
            or operation == "evidence.authorization.create"
        ):
            permission_operation = "authorizations:write"
        else:
            permission_operation = "evidence:write"
        current_actor(
            self.actor(request),
            tenant,
            self.write_permission or permission_operation,
            project=project,
        )
        for extra in self.additional_write_operations:
            current_actor(self.actor(request), tenant, extra, project=project)
        # The shared helper binds the JSON body and path. Bind query-scoped
        # project/purpose too, including when replay bypasses the callback.
        import hashlib
        import json

        operation = (
            "governed:"
            + hashlib.sha256(
                json.dumps(
                    [
                        operation,
                        sorted(
                            (key, request.query_params.getlist(key))
                            for key in request.query_params
                        ),
                    ],
                    ensure_ascii=False,
                ).encode()
            ).hexdigest()
        )
        claim = begin_idempotent_request(
            request=request, tenant=tenant, operation=operation
        )
        if claim.is_replay:
            return success_response(
                claim.response_data, request=request, status=claim.response_status
            )
        data = callback()
        complete_idempotent_request(claim, response_data=data, response_status=status)
        return success_response(data, request=request, status=status)

    def handle_exception(self, exc):
        if isinstance(exc, ModelValidationError):
            exc = ValidationError(getattr(exc, "message_dict", exc.messages))
        elif isinstance(exc, ConsentProofUnavailable):
            exc = PurposeProofUnavailable()
        return super().handle_exception(exc)


class SchemaListView(GovernedAPIView):
    write_permission = "schemas:write"

    @transaction.atomic
    def get(self, request):
        tenant, _, _ = _scope(self.tenant(request).pk)
        kind = request.query_params.get("kind", "evidence")
        if kind not in {"evidence", "claim"}:
            raise ValidationError("Choose evidence or claim schemas.")
        current_actor(
            self.actor(request),
            tenant,
            "claims:read" if kind == "claim" else "evidence:read",
        )
        items, pagination = paginate_cursor_results(
            ResourceSchema.objects.filter(
                tenant=tenant, kind=kind, retired_at__isnull=True
            ),
            request,
            cursor_scope=f"schemas:{tenant.public_id}:{kind}",
        )
        return success_response(
            {
                "results": [schema_summary(item) for item in items],
                "pagination": pagination,
            },
            request=request,
        )

    def post(self, request):
        data = self.parsed(SchemaInput, request.data)
        return self.write(
            request,
            "evidence.schema.create",
            lambda: schema_summary(
                create_schema(
                    tenant_id=self.tenant(request).pk,
                    actor=self.actor(request),
                    request=request,
                    **data,
                )
            ),
        )


class AuthorizationListView(GovernedAPIView):
    read_permission = "authorizations:write"
    write_permission = "authorizations:write"

    @transaction.atomic
    def get(self, request):
        tenant, _, _ = _scope(self.tenant(request).pk)
        current_actor(self.actor(request), tenant, "authorizations:write")
        query = PurposeAuthorization.objects.select_related(
            "project", "subject"
        ).filter(tenant=tenant)
        items, pagination = paginate_cursor_results(
            query, request, cursor_scope=f"purpose-authorizations:{tenant.public_id}"
        )
        return success_response(
            {
                "results": [authorization_summary(item) for item in items],
                "pagination": pagination,
            },
            request=request,
        )

    def post(self, request):
        data = self.parsed(AuthorizationInput, request.data)
        return self.write(
            request,
            "evidence.authorization.create",
            lambda: authorization_summary(
                propose_authorization(
                    tenant_id=self.tenant(request).pk,
                    actor=self.actor(request),
                    request=request,
                    **data,
                )
            ),
        )


class AuthorizationApproveView(GovernedAPIView):
    write_permission = "authorizations:approve"

    def post(self, request, authorization_id):
        from apps.evidence.serializers import EmptyInput

        self.parsed(EmptyInput, request.data)
        return self.write(
            request,
            f"purpose.approve:{authorization_id}",
            lambda: authorization_summary(
                approve_authorization(
                    tenant_id=self.tenant(request).pk,
                    actor=self.actor(request),
                    authorization_id=authorization_id,
                    request=request,
                )
            ),
            status=200,
        )


class AuthorizationRevokeView(GovernedAPIView):
    write_permission = "authorizations:write"

    def post(self, request, authorization_id):
        data = self.parsed(RevokeInput, request.data)
        return self.write(
            request,
            f"purpose.revoke:{authorization_id}",
            lambda: authorization_summary(
                revoke_authorization(
                    tenant_id=self.tenant(request).pk,
                    actor=self.actor(request),
                    authorization_id=authorization_id,
                    request=request,
                    **data,
                )
            ),
            status=200,
        )


class EvidenceListView(GovernedAPIView):
    @transaction.atomic
    def get(self, request):
        data = self.parsed(ResourceQuery, request.query_params)
        tenant, project, _ = _scope(self.tenant(request).pk, data["project_id"])
        actor = current_actor(
            self.actor(request), tenant, "evidence:read", project=project
        )
        now = timezone.now()
        query = Evidence.objects.filter(
            tenant=tenant,
            project=project,
            purpose=data["purpose"],
            status="active",
            deleted_at__isnull=True,
            valid_until__gt=now,
            delete_after__gt=now,
        )
        items, pagination = paginate_cursor_results(
            query,
            request,
            cursor_scope=f"evidence:{tenant.public_id}:{project.public_id}:{actor.public_id}",
        )
        result = []
        for item in items:
            try:
                result.append(
                    read_evidence(
                        tenant_id=tenant.pk,
                        actor=actor,
                        evidence_id=item.public_id,
                        request=request,
                        **data,
                    )
                )
            except PermissionDenied:
                # Page position is stable even if a source/authorization ceased
                # being usable. Do not return stale payloads or exception text.
                continue
        return success_response(
            {"results": result, "pagination": pagination}, request=request
        )

    def post(self, request):
        data = self.parsed(EvidenceInput, request.data)

        def create():
            item = create_evidence(
                tenant_id=self.tenant(request).pk,
                actor=self.actor(request),
                request=request,
                **data,
            )
            return {
                "id": item.public_id,
                "status": item.status,
                "schema_id": item.schema.public_id,
                "created_at": item.created_at.isoformat(),
            }

        return self.write(request, "evidence.create", create)


class EvidenceDetailView(GovernedAPIView):
    def get(self, request, evidence_id):
        data = self.parsed(ResourceQuery, request.query_params)
        return success_response(
            read_evidence(
                tenant_id=self.tenant(request).pk,
                actor=self.actor(request),
                evidence_id=evidence_id,
                request=request,
                **data,
            ),
            request=request,
        )


class EvidenceLineageView(GovernedAPIView):
    @transaction.atomic
    def get(self, request, evidence_id):
        data = self.parsed(ResourceQuery, request.query_params)
        tenant, project, _ = _scope(self.tenant(request).pk, data["project_id"])
        actor = current_actor(
            self.actor(request), tenant, "evidence:read", project=project
        )
        root = get_object_or_404(
            Evidence.objects.select_related(
                "authorization__tenant",
                "authorization__project",
                "authorization__subject",
                "authorization__consent_record__verification",
            ),
            tenant=tenant,
            project=project,
            purpose=data["purpose"],
            public_id=evidence_id,
        )
        nodes = ancestry(root)
        edges = EvidenceSource.objects.filter(
            evidence_id__in=nodes, source_id__in=nodes
        ).order_by("evidence_id", "source_id")
        payload = {
            "root_id": root.public_id,
            "nodes": [
                {
                    "id": item.public_id,
                    "schema_id": item.schema.public_id,
                    "evidence_type": item.evidence_type,
                    "status": item.status,
                }
                for item in sorted(nodes.values(), key=lambda item: item.pk)
            ],
            "edges": [
                {
                    "resource_id": nodes[edge.evidence_id].public_id,
                    "source_id": nodes[edge.source_id].public_id,
                }
                for edge in edges
            ],
            "truncated": False,
        }
        record_audit_event(
            tenant=tenant,
            actor=actor,
            action="evidence.lineage_accessed",
            target_type="evidence",
            target_id=root.public_id,
            request=request,
            metadata={"node_count": len(nodes)},
        )
        return success_response(payload, request=request)


class EvidenceRevokeView(GovernedAPIView):
    def post(self, request, evidence_id):
        scope = self.parsed(ResourceQuery, request.query_params)
        scope.pop("include_payload")
        data = self.parsed(RevokeInput, request.data)

        def revoke():
            record = revoke_evidence(
                tenant_id=self.tenant(request).pk,
                actor=self.actor(request),
                evidence_id=evidence_id,
                request=request,
                **scope,
                **data,
            )
            return {"id": record.public_id, "status": record.status}

        return self.write(request, f"evidence.revoke:{evidence_id}", revoke, status=200)


class SchemaDetailView(GovernedAPIView):
    @transaction.atomic
    def get(self, request, schema_id):
        tenant, _, _ = _scope(self.tenant(request).pk)
        kind = request.query_params.get("kind", "evidence")
        if kind not in {"evidence", "claim"}:
            raise ValidationError("Choose evidence or claim schemas.")
        current_actor(
            self.actor(request),
            tenant,
            "claims:read" if kind == "claim" else "evidence:read",
        )
        record = get_object_or_404(
            ResourceSchema, tenant=tenant, public_id=schema_id, kind=kind
        )
        return success_response(schema_summary(record), request=request)


class SchemaRetireView(GovernedAPIView):
    write_permission = "schemas:write"

    def post(self, request, schema_id):
        from apps.evidence.serializers import EmptyInput

        self.parsed(EmptyInput, request.data)
        from apps.evidence.services import retire_schema

        return self.write(
            request,
            f"schema.retire:{schema_id}",
            lambda: schema_summary(
                retire_schema(
                    tenant_id=self.tenant(request).pk,
                    actor=self.actor(request),
                    schema_id=schema_id,
                    request=request,
                )
            ),
            status=200,
        )


class HoldListView(GovernedAPIView):
    read_permission = "authorizations:write"
    write_permission = "authorizations:write"
    allow_inactive_write_context = True

    @transaction.atomic
    def get(self, request):
        from apps.evidence.models import ResourceLegalHold
        from apps.evidence.serializers import hold_summary

        tenant, _, _ = _scope(self.tenant(request).pk)
        current_actor(self.actor(request), tenant, "authorizations:write")
        items, pagination = paginate_cursor_results(
            ResourceLegalHold.objects.select_related("project", "subject").filter(
                tenant=tenant
            ),
            request,
            cursor_scope=f"resource-holds:{tenant.public_id}",
        )
        return success_response(
            {
                "results": [hold_summary(item) for item in items],
                "pagination": pagination,
            },
            request=request,
        )

    def post(self, request):
        from apps.evidence.lifecycle import create_legal_hold
        from apps.evidence.serializers import HoldInput, hold_summary

        data = self.parsed(HoldInput, request.data)
        return self.write(
            request,
            "resource-hold.create",
            lambda: hold_summary(
                create_legal_hold(
                    tenant_id=self.tenant(request).pk,
                    actor=self.actor(request),
                    request=request,
                    **data,
                )
            ),
        )


class HoldReleaseView(GovernedAPIView):
    write_permission = "authorizations:write"
    allow_inactive_write_context = True

    def post(self, request, hold_id):
        from apps.evidence.serializers import EmptyInput

        self.parsed(EmptyInput, request.data)
        from apps.evidence.lifecycle import release_legal_hold
        from apps.evidence.serializers import hold_summary

        return self.write(
            request,
            f"resource-hold.release:{hold_id}",
            lambda: hold_summary(
                release_legal_hold(
                    tenant_id=self.tenant(request).pk,
                    actor=self.actor(request),
                    hold_id=hold_id,
                    request=request,
                )
            ),
            status=200,
        )


class AuthorizationDetailView(GovernedAPIView):
    read_permission = "authorizations:write"

    @transaction.atomic
    def get(self, request, authorization_id):
        from apps.evidence.access import protected_value
        from apps.evidence.services import _audit

        tenant, _, _ = _scope(self.tenant(request).pk)
        actor = current_actor(self.actor(request), tenant, "authorizations:write")
        item = get_object_or_404(
            PurposeAuthorization.objects.select_related("tenant", "project", "subject"),
            tenant=tenant,
            public_id=authorization_id,
        )
        payload = authorization_summary(item)
        payload["justification"] = protected_value(item, "justification_json")
        payload["proposed_by_id"] = item.proposed_by_id_snapshot
        payload["approved_by_id"] = item.approved_by_id_snapshot or None
        payload["consent_record_id"] = (
            item.consent_record.public_id if item.consent_record_id else None
        )
        _audit(item, actor, "evidence.authorization_reviewed", request)
        return success_response(payload, request=request)


class HoldDetailView(GovernedAPIView):
    read_permission = "authorizations:write"

    @transaction.atomic
    def get(self, request, hold_id):
        from apps.evidence.access import protected_value
        from apps.evidence.models import ResourceLegalHold
        from apps.evidence.serializers import hold_summary
        from apps.evidence.services import _audit

        tenant, _, _ = _scope(self.tenant(request).pk)
        actor = current_actor(self.actor(request), tenant, "authorizations:write")
        item = get_object_or_404(
            ResourceLegalHold.objects.select_related("tenant", "project", "subject"),
            tenant=tenant,
            public_id=hold_id,
        )
        payload = {**hold_summary(item), "reason": protected_value(item, "reason_json")}
        _audit(item, actor, "evidence.legal_hold_reviewed", request)
        return success_response(payload, request=request)
