from django.conf.urls import url
from .views import PostcodeView, AddressView

urlpatterns = [
    url(
        r"^postcode/(?P<postcode>[A-Za-z0-9 +]+)/$",
        PostcodeView.as_view(),
        name="v1-postcode",
    ),
    url(r"^address/(?P<slug>[-\w]+)/$", AddressView.as_view(), name="v1-address"),
]
