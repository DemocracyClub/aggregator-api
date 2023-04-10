import os

from apiblueprint_view.views import ApiBlueprintView
from django.conf import settings
from django.core.management.base import BaseCommand
from django.http import HttpRequest


class Command(BaseCommand):
    def handle(self, *args, **options):
        request = HttpRequest()
        request.method = "GET"
        request.META["REMOTE_ADDR"] = "localhost"
        request.path = "/foo/bar/"

        view = ApiBlueprintView.as_view(
            blueprint=os.path.join(
                settings.BASE_DIR, "apps/api_docs/v1/docs/documentation.apibp"
            ),
            template_name="api_docs_template.html",
            styles={
                "resource": {"class": "card"},
                "resource_group": {"class": "card"},
                "method_GET": {"class": "badge success"},
            },
        )

        response = view(request)
        outfile = os.path.join(
            settings.BASE_DIR,
            "apps/api_docs/v1/templates/api_docs_rendered.html",
        )
        with open(outfile, "w") as f:
            f.write(response.rendered_content)
