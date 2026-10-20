from django.db import transaction
from rest_framework import serializers

from apps.evidence.access import protected_value
from apps.evidence.serializers import StrictInput
from apps.evidence.services import _audit
from apps.evidence.views import GovernedAPIView
from apps.providers import assurance
from apps.providers.models import ProviderCertification
from common.pagination import paginate_cursor_results
from common.responses import success_response


class CertificationInput(StrictInput):
    configuration_id = serializers.CharField(max_length=64)
    capability = serializers.CharField(max_length=32)
    report = serializers.DictField(allow_empty=False)
    assurance_level = serializers.ChoiceField(choices=["conformance", "assured"])
    valid_until = serializers.DateTimeField()
    delete_after = serializers.DateTimeField()


class ConfigurationQuery(serializers.Serializer):
    configuration_id = serializers.CharField(max_length=64)
    capability = serializers.CharField(max_length=32, required=False)


class CertificationRevokeInput(StrictInput):
    reason = serializers.RegexField(r"^[a-z][a-z0-9_]{0,119}$")


class EmptyInput(StrictInput):
    pass


class AssuranceAPIView(GovernedAPIView):
    read_permission = "providers:assurance"
    write_permission = "providers:assurance"


class CertificationListView(AssuranceAPIView):
    @transaction.atomic
    def get(self, request):
        data = self.parsed(ConfigurationQuery, request.query_params)
        actor, config = assurance._config(
            self.tenant(request).pk,
            self.actor(request),
            data["configuration_id"],
            "providers:assurance",
        )
        query = ProviderCertification.objects.select_related("configuration").filter(
            tenant_id=config.provider.tenant_id,
            configuration=config,
        )
        if data.get("capability"):
            query = query.filter(capability=data["capability"])
        records, pagination = paginate_cursor_results(
            query,
            request,
            cursor_scope=f"certifications:{config.public_id}:{actor.public_id}",
        )
        return success_response(
            {
                "results": [assurance.summary(record) for record in records],
                "pagination": pagination,
            },
            request=request,
        )

    def post(self, request):
        data = self.parsed(CertificationInput, request.data)
        return self.write(
            request,
            "providers.certification.create",
            lambda: assurance.summary(
                assurance.propose_certification(
                    tenant_id=self.tenant(request).pk,
                    actor=self.actor(request),
                    request=request,
                    **data,
                )
            ),
        )


class CertificationScopeView(AssuranceAPIView):
    @transaction.atomic
    def get(self, request):
        data = self.parsed(ConfigurationQuery, request.query_params)
        actor, config = assurance._config(
            self.tenant(request).pk,
            self.actor(request),
            data["configuration_id"],
            "providers:assurance",
        )
        if not data.get("capability"):
            raise serializers.ValidationError("A capability is required.")
        scope = assurance.report_scope(config, data["capability"])
        cases = assurance.SYNC_CASES | (
            assurance.ASYNC_CASES if scope["operation_contract"] != "sync" else set()
        )
        return success_response(
            {**scope, "required_cases": sorted(cases)}, request=request
        )


class CertificationDetailView(AssuranceAPIView):
    @transaction.atomic
    def get(self, request, certification_id):
        actor, record = assurance._record(
            self.tenant(request).pk,
            self.actor(request),
            certification_id,
            "providers:assurance",
        )
        _audit(record, actor, "provider.certification_report_accessed", request)
        return success_response(
            {
                **assurance.summary(record),
                "report": protected_value(record, "report_json"),
            },
            request=request,
        )


class CertificationApproveView(AssuranceAPIView):
    write_permission = "providers:assurance:approve"
    additional_write_operations = ("providers:assurance",)

    def post(self, request, certification_id):
        self.parsed(EmptyInput, request.data)
        return self.write(
            request,
            f"providers.certification.approve:{certification_id}",
            lambda: assurance.summary(
                assurance.approve_certification(
                    tenant_id=self.tenant(request).pk,
                    actor=self.actor(request),
                    certification_id=certification_id,
                    request=request,
                )
            ),
            status=200,
        )


class CertificationRevokeView(AssuranceAPIView):
    def post(self, request, certification_id):
        data = self.parsed(CertificationRevokeInput, request.data)
        return self.write(
            request,
            f"providers.certification.revoke:{certification_id}",
            lambda: assurance.summary(
                assurance.revoke_certification(
                    tenant_id=self.tenant(request).pk,
                    actor=self.actor(request),
                    certification_id=certification_id,
                    request=request,
                    **data,
                )
            ),
            status=200,
        )
