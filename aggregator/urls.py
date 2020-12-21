from django.conf.urls import url, include
from django.views.generic import TemplateView

urlpatterns = [
    url(r"^api/", include(("api.urls", "api"), namespace="api")),
    url(r"^$", TemplateView.as_view(template_name="home.html"), name="home"),
    url(r"^terms/$", TemplateView.as_view(template_name="terms.html"), name="terms"),
]

handler500 = "dc_theme.urls.dc_server_error"
