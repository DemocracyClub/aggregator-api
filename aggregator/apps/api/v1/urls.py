from django.urls import re_path, path
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
    re_path(
        r"^postcode/(?P<postcode>[A-Za-z0-9 +]+)/$",
        PostcodeView.as_view(),
        name="postcode",
    ),
    re_path(r"^address/(?P<slug>[-\w]+)/$", AddressView.as_view(), name="address"),
    re_path(
        r"^elections/(?P<slug>[\w.-]+)/$",
        SingleElectionView.as_view(),
        name="elections_get",
    ),
    path("elections/", ElectionListView.as_view(), name="elections_list"),
    # sandbox endpoints
    re_path(
        r"^sandbox/postcode/(?P<postcode>[A-Za-z0-9 +]+)/$",
        SandboxView.as_view(),
        name="sandbox-postcode",
    ),
    re_path(
        r"^sandbox/address/(?P<slug>[-\w]+)/$",
        SandboxView.as_view(),
        name="sandbox-address",
    ),
    # docs root
    path("", TemplateView.as_view(template_name="api_docs_rendered.html"), name="docs"),
    # redirect these to the docs instead of throwing a 404
    path("postcode/", docs_redirect),
    path("address/", docs_redirect),
    path("sandbox/postcode/", docs_redirect),
    path("sandbox/address/", docs_redirect),
    path("sandbox/elections/", docs_redirect),
    path("sandbox/", docs_redirect),
]
