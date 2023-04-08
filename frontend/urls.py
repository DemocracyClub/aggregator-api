from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path(
        r"terms/",
        TemplateView.as_view(template_name="terms.html"),
        name="terms",
    ),
    path(
        r"api/v1/",
        TemplateView.as_view(template_name="api_docs_rendered.html"),
        name="docs",
    ),
]

handler500 = "dc_utils.urls.dc_server_error"
