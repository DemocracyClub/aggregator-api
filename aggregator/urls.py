from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("api/", include(("api.urls", "api"), namespace="api")),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path(r"terms/", TemplateView.as_view(template_name="terms.html"), name="terms"),
]

handler500 = "dc_theme.urls.dc_server_error"
