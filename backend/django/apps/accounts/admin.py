from django.contrib import admin

from apps.accounts.models import ContactInquiry, PasswordResetToken, PlatformUser


@admin.register(PlatformUser)
class PlatformUserAdmin(admin.ModelAdmin):
    list_display = ("email", "public_id", "tenant", "status", "is_platform_admin", "mfa_enabled")
    list_filter = ("status", "is_platform_admin", "mfa_enabled", "is_staff")
    search_fields = ("email", "public_id", "first_name", "last_name")


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("public_id", "user", "expires_at", "used_at", "revoked_at")
    search_fields = ("public_id", "user__email")
    list_filter = ("used_at", "revoked_at")


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ("public_id", "full_name", "business_email", "interest", "status", "created_at")
    search_fields = ("public_id", "full_name", "business_email", "organization_name")
    list_filter = ("status", "interest")
