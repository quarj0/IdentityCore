from rest_framework import serializers

from apps.verification_policies.models import VerificationPolicy
from common.catalog import DOCUMENT_TYPES

VALID_DOCUMENT_TYPES = {item["code"] for item in DOCUMENT_TYPES}


def serialize_verification_policy(policy: VerificationPolicy) -> dict:
    return {
        "id": policy.public_id,
        "project_id": policy.project.public_id if policy.project else None,
        "name": policy.name,
        "description": policy.description,
        "consent_template_id": policy.consent_template.public_id if policy.consent_template else None,
        "default_locale": policy.default_locale,
        "supported_locales": policy.supported_locales_json or [policy.default_locale],
        "version": policy.version,
        "status": policy.status,
        "required_document_types": policy.required_document_types,
        "required_liveness_level": policy.required_liveness_level,
        "face_match_threshold": float(policy.face_match_threshold),
        "manual_review_threshold": float(policy.manual_review_threshold),
        "maker_checker_required": policy.maker_checker_required,
        "verification_expiry_minutes": policy.verification_expiry_minutes,
        "media_retention_days": policy.media_retention_days,
        "metadata_retention_days": policy.metadata_retention_days,
        "created_at": policy.created_at.isoformat(),
        "updated_at": policy.updated_at.isoformat(),
    }


class VerificationPolicyCreateSerializer(serializers.Serializer):
    project_id = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    consent_template_id = serializers.CharField(required=False, allow_blank=True)
    default_locale = serializers.CharField(max_length=16, required=False, default="en")
    supported_locales = serializers.ListField(
        child=serializers.CharField(max_length=16), required=False, default=list
    )
    required_document_types = serializers.ListField(
        child=serializers.CharField(max_length=64),
        allow_empty=False,
    )
    required_liveness_level = serializers.ChoiceField(
        choices=[("passive", "Passive"), ("active", "Active")]
    )
    face_match_threshold = serializers.DecimalField(max_digits=5, decimal_places=4)
    manual_review_threshold = serializers.DecimalField(max_digits=5, decimal_places=4)
    maker_checker_required = serializers.BooleanField(required=False, default=False)
    verification_expiry_minutes = serializers.IntegerField(min_value=1)
    media_retention_days = serializers.IntegerField(min_value=1)
    metadata_retention_days = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        tenant = self.context["request"].user.tenant
        unknown = set(attrs["required_document_types"]) - VALID_DOCUMENT_TYPES
        if unknown:
            raise serializers.ValidationError(
                {"required_document_types": "Choose only supported document types."}
            )
        if attrs["manual_review_threshold"] > attrs["face_match_threshold"]:
            raise serializers.ValidationError(
                {
                    "manual_review_threshold": "Manual review threshold must not exceed the face match threshold."
                }
            )
        template_id = attrs.get("consent_template_id", "")
        if template_id:
            template = tenant.consent_templates.filter(
                public_id=template_id, status="active"
            ).first()
            if template is None:
                raise serializers.ValidationError(
                    {"consent_template_id": "Choose an active consent template."}
                )
            attrs["consent_template"] = template
        locales = list(dict.fromkeys(attrs.get("supported_locales") or []))
        default_locale = attrs.get("default_locale", "en")
        if default_locale not in locales:
            locales.insert(0, default_locale)
        if attrs.get("consent_template") and attrs["consent_template"].language != default_locale:
            raise serializers.ValidationError(
                {"default_locale": "The default locale must match the consent template language."}
            )
        attrs["supported_locales"] = locales
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        tenant = request.user.tenant
        name = validated_data["name"]
        latest_policy = (
            tenant.verification_policies.filter(name=name).order_by("-version").first()
        )
        next_version = 1 if latest_policy is None else latest_policy.version + 1
        return VerificationPolicy.objects.create(
            tenant=tenant,
            project=tenant.projects.filter(
                public_id=validated_data.get("project_id")
            ).first()
            or tenant.projects.filter(is_default=True).first(),
            name=name,
            description=validated_data.get("description", ""),
            consent_template=validated_data.get("consent_template"),
            default_locale=validated_data["default_locale"],
            supported_locales_json=validated_data["supported_locales"],
            version=next_version,
            status="draft",
            required_document_types_json=validated_data["required_document_types"],
            required_liveness_level=validated_data["required_liveness_level"],
            face_match_threshold=validated_data["face_match_threshold"],
            manual_review_threshold=validated_data["manual_review_threshold"],
            maker_checker_required=validated_data["maker_checker_required"],
            verification_expiry_minutes=validated_data["verification_expiry_minutes"],
            media_retention_days=validated_data["media_retention_days"],
            metadata_retention_days=validated_data["metadata_retention_days"],
            created_by=request.user,
        )


class VerificationPolicyUpdateSerializer(VerificationPolicyCreateSerializer):
    name = serializers.CharField(max_length=255, required=False)
    consent_template_id = serializers.CharField(required=False, allow_blank=True)
    default_locale = serializers.CharField(max_length=16, required=False)
    supported_locales = serializers.ListField(
        child=serializers.CharField(max_length=16), required=False
    )
    required_document_types = serializers.ListField(
        child=serializers.CharField(max_length=64), required=False, allow_empty=False
    )
    required_liveness_level = serializers.ChoiceField(
        choices=[("passive", "Passive"), ("active", "Active")], required=False
    )
    face_match_threshold = serializers.DecimalField(
        max_digits=5, decimal_places=4, required=False
    )
    manual_review_threshold = serializers.DecimalField(
        max_digits=5, decimal_places=4, required=False
    )
    maker_checker_required = serializers.BooleanField(required=False)
    verification_expiry_minutes = serializers.IntegerField(min_value=1, required=False)
    media_retention_days = serializers.IntegerField(min_value=1, required=False)
    metadata_retention_days = serializers.IntegerField(min_value=1, required=False)

    def validate(self, attrs):
        policy = self.instance
        unknown = set(attrs.get("required_document_types", [])) - VALID_DOCUMENT_TYPES
        if unknown:
            raise serializers.ValidationError(
                {"required_document_types": "Choose only supported document types."}
            )
        manual_threshold = attrs.get(
            "manual_review_threshold", policy.manual_review_threshold
        )
        face_threshold = attrs.get("face_match_threshold", policy.face_match_threshold)
        if manual_threshold > face_threshold:
            raise serializers.ValidationError(
                {
                    "manual_review_threshold": "Manual review threshold must not exceed the face match threshold."
                }
            )
        if "consent_template_id" in attrs:
            template_id = attrs.get("consent_template_id", "")
            template = (
                self.context["request"].user.tenant.consent_templates.filter(
                    public_id=template_id, status="active"
                ).first()
                if template_id
                else None
            )
            if template_id and template is None:
                raise serializers.ValidationError(
                    {"consent_template_id": "Choose an active consent template."}
                )
            attrs["consent_template"] = template
        default_locale = attrs.get("default_locale", policy.default_locale)
        locales = list(
            dict.fromkeys(
                attrs.get("supported_locales", policy.supported_locales_json) or []
            )
        )
        if default_locale not in locales:
            locales.insert(0, default_locale)
        template = attrs.get("consent_template", policy.consent_template)
        if template and template.language != default_locale:
            raise serializers.ValidationError(
                {"default_locale": "The default locale must match the consent template language."}
            )
        attrs["supported_locales"] = locales
        return attrs

    def update(self, instance, validated_data):
        if instance.status != "draft":
            raise serializers.ValidationError(
                {"status": "Only draft templates can be edited."}
            )
        for field, value in validated_data.items():
            if field == "consent_template_id":
                continue
            model_field = (
                "required_document_types_json"
                if field == "required_document_types"
                else "supported_locales_json"
                if field == "supported_locales"
                else field
            )
            setattr(instance, model_field, value)
        instance.save()
        return instance
