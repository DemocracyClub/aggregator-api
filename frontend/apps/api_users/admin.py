from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path

from api_users.dynamodb_helpers import DynamoDBClient
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

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "sync_api_keys/",
                self.admin_site.admin_view(self.sync_api_keys),
                name="sync_api_keys",
            )
        ]
        return my_urls + urls

    def sync_api_keys(self, request):
        DynamoDBClient().sync_api_keys()

        return TemplateResponse(request, "admin/sync_confirmation.html")


admin.site.register(CustomUser, ApiUserAdmin)
