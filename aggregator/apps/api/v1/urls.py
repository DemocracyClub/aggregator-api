from django.conf.urls import url
from django.urls import reverse_lazy
from django.views.generic import RedirectView, TemplateView
from .views import AddressView, PostcodeView, SandboxView

docs_redirect = RedirectView.as_view(url=reverse_lazy("api:v1:docs"), permanent=True)

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
    url(
        r"^$", TemplateView.as_view(template_name="api_docs_rendered.html"), name="docs"
    ),
    url(r"^postcode/$", docs_redirect),
    url(r"^address/$", docs_redirect),
    url(r"^sandbox/postcode/$", docs_redirect),
    url(r"^sandbox/address/$", docs_redirect),
    url(r"^sandbox/$", docs_redirect),
]
