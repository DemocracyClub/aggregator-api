from django.conf.urls import url
from django.views.generic import TemplateView
from .views import AddressView, PostcodeView, SandboxView

urlpatterns = [
    url(
        r"^postcode/(?P<postcode>[A-Za-z0-9 +]+)/$",
        PostcodeView.as_view(),
        name="postcode",
    ),
    url(r"^address/(?P<slug>[-\w]+)/$", AddressView.as_view(), name="address"),
    url(
        r"^sandbox/postcode/(?P<postcode>[A-Za-z0-9 +]+)/$",
        SandboxView.as_view(),
        name="sandbox-postcode",
    ),
    url(
        r"^sandbox/address/(?P<slug>[-\w]+)/$",
        SandboxView.as_view(),
        name="sandbox-address",
    ),
    url(r"^$", TemplateView.as_view(template_name="api_docs_rendered.html")),
]
