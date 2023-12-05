from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path(
        r"terms/",
        TemplateView.as_view(template_name="terms.html"),
        name="terms",
    ),
    path(
        r"api/v1/",
        TemplateView.as_view(template_name="api_docs_rendered_base.html"),
        name="docs",
    ),
    path("user/", include("api_users.urls", namespace="api_users")),
]

handler500 = "dc_utils.urls.dc_server_error"
