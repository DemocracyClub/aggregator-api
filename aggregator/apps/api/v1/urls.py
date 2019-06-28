from django.conf.urls import url
from django.urls import reverse_lazy
from django.views.generic import RedirectView, TemplateView
from .views import (
    AddressView,
    PostcodeView,
    ElectionListView,
    SingleElectionView,
    SandboxView,
)

docs_redirect = RedirectView.as_view(url=reverse_lazy("api:v1:docs"))

urlpatterns = [
    # API endpoints
    url(
        r"^postcode/(?P<postcode>[A-Za-z0-9 +]+)/$",
        PostcodeView.as_view(),
        name="postcode",
    ),
    url(r"^address/(?P<slug>[-\w]+)/$", AddressView.as_view(), name="address"),
    url(
        r"^elections/(?P<slug>[\w.-]+)/$",
        SingleElectionView.as_view(),
        name="elections_get",
    ),
    url(r"^elections/$", ElectionListView.as_view(), name="elections_list"),
    # sandbox endpoints
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
    # docs root
    url(
        r"^$", TemplateView.as_view(template_name="api_docs_rendered.html"), name="docs"
    ),
    # redirect these to the docs instead of throwing a 404
    url(r"^postcode/$", docs_redirect),
    url(r"^address/$", docs_redirect),
    url(r"^sandbox/postcode/$", docs_redirect),
    url(r"^sandbox/address/$", docs_redirect),
    url(r"^sandbox/elections/$", docs_redirect),
    url(r"^sandbox/$", docs_redirect),
]
