from django.conf.urls import url, include
from django.urls import reverse_lazy
from django.views.generic import RedirectView

urlpatterns = [
    url(r"^v1/", include(("api.v1.urls", "v1"), namespace="v1")),
    url(r"^$", RedirectView.as_view(url=reverse_lazy("api:v1:docs"), permanent=True)),
]
