from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^api/", include("api.urls", namespace="api")),
    url(r"^$", TemplateView.as_view(template_name="home.html")),
]

handler500 = "dc_theme.urls.dc_server_error"
