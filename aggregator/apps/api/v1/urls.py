from django.conf.urls import url
from .views import AddressView, PostcodeView, SandboxView

urlpatterns = [
    url(
        r"^postcode/(?P<postcode>[A-Za-z0-9 +]+)/$",
        PostcodeView.as_view(),
        name="v1-postcode",
    ),
    url(r"^address/(?P<slug>[-\w]+)/$", AddressView.as_view(), name="v1-address"),
    url(
        r"^sandbox/postcode/(?P<postcode>[A-Za-z0-9 +]+)/$",
        SandboxView.as_view(),
        name="v1-sandbox-postcode",
    ),
    url(
        r"^sandbox/address/(?P<slug>[-\w]+)/$",
        SandboxView.as_view(),
        name="v1-sandbox-address",
    ),
]
