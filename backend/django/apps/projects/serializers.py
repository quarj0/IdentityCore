from django.utils.text import slugify
from rest_framework import serializers

from apps.organizations.models import OrganizationStatus
from apps.projects.models import Project, ProjectEnvironment


def serialize_project(project):
    return {
        "id": project.public_id,
        "name": project.name,
        "slug": project.slug,
        "environment": project.environment,
        "status": project.status,
        "allowed_origins": project.allowed_origins,
        "is_default": project.is_default,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


class ProjectSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=255, required=False)
    environment = serializers.ChoiceField(
        choices=ProjectEnvironment.choices, default=ProjectEnvironment.SANDBOX
    )
    allowed_origins = serializers.ListField(
        child=serializers.URLField(), required=False, default=list
    )

    def validate(self, attrs):
        tenant = self.context["request"].user.tenant
        if (
            attrs.get("environment") == ProjectEnvironment.PRODUCTION
            and tenant.organization.status != OrganizationStatus.ACTIVE
        ):
            raise serializers.ValidationError(
                {"environment": "Production projects require an approved organization."}
            )
        if self.instance is None and tenant.organization.status != OrganizationStatus.ACTIVE and tenant.projects.exists():
            raise serializers.ValidationError(
                {"environment": "Pending workspaces are limited to one sandbox project."}
            )
        slug = attrs.get("slug") or slugify(attrs["name"])
        if (
            Project.objects.filter(tenant=tenant, slug=slug)
            .exclude(pk=getattr(self.instance, "pk", None))
            .exists()
        ):
            raise serializers.ValidationError(
                {"slug": "A project with this slug already exists."}
            )
        attrs["slug"] = slug
        return attrs

    def create(self, data):
        return Project.objects.create(
            tenant=self.context["request"].user.tenant,
            created_by=self.context["request"].user,
            name=data["name"],
            slug=data["slug"],
            environment=data["environment"],
            allowed_origins_json=data["allowed_origins"],
        )

    def update(self, instance, data):
        for field in ("name", "slug", "environment"):
            if field in data:
                setattr(instance, field, data[field])
        if "allowed_origins" in data:
            instance.allowed_origins_json = data["allowed_origins"]
        instance.save()
        return instance
