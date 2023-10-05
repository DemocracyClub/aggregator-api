from django.contrib import admin

from api_users.models import APIKey, CustomUser


class ApiKeyInline(admin.TabularInline):
    model = APIKey
    extra = 0
    can_delete = True
    fields = (
        "name",
        "usage_reason",
        "rate_limit_warn",
        "is_active",
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    readonly_fields = ("name", "key", "usage_reason")


class ApiUserAdmin(admin.ModelAdmin):
    search_fields = ("email",)

    fields = ("name", "email", "api_plan")

    inlines = [ApiKeyInline]


admin.site.register(CustomUser, ApiUserAdmin)
