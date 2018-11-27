import abc
import asyncio
import aiohttp
import json
import os
import re
from django.http import HttpResponse
from django.views import View
from .api_client import ApiClient, ApiError
from .stitcher import Stitcher, StitcherValidationError


class BaseView(View, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_response(self, request, *args, **kwargs):
        pass

    def get(self, request, *args, **kwargs):

        auth_header = request.META.get("HTTP_AUTHORIZATION", None)
        auth_param = request.GET.get("auth_token", None)
        if (not auth_param and not auth_header) or (
            auth_header and not re.match(r"Token .*", auth_header)
        ):
            return HttpResponse(
                json.dumps({"message": "Invalid token."}),
                content_type="application/json",
                status=401,
            )

        try:
            return self.get_response(request, *args, **kwargs)
        except ApiError as e:
            return HttpResponse(
                json.dumps({"message": e.message}),
                content_type="application/json",
                status=e.status,
            )
        except (asyncio.TimeoutError, aiohttp.ClientConnectorError):
            return HttpResponse(
                json.dumps({"message": "Backend Connection Error"}),
                content_type="application/json",
                status=500,
            )


class PostcodeView(BaseView):
    def get_response(self, request, *args, **kwargs):
        client = ApiClient()
        wdiv, wcivf = client.get_data_for_postcode(kwargs["postcode"])

        try:
            stitcher = Stitcher(wdiv, wcivf, request)
        except StitcherValidationError:
            return HttpResponse(
                json.dumps({"message": "Internal Server Error"}),
                content_type="application/json",
                status=500,
            )

        if not wdiv["polling_station_known"] and len(wdiv["addresses"]) > 0:
            result = stitcher.make_address_picker_response()
        else:
            result = stitcher.make_result_known_response()

        return HttpResponse(
            json.dumps(result), content_type="application/json", status=200
        )


class AddressView(BaseView):
    def get_response(self, request, *args, **kwargs):
        client = ApiClient()
        wdiv, wcivf = client.get_data_for_address(kwargs["slug"])

        try:
            stitcher = Stitcher(wdiv, wcivf, request)
        except StitcherValidationError:
            return HttpResponse(
                json.dumps({"message": "Internal Server Error"}),
                content_type="application/json",
                status=500,
            )

        result = stitcher.make_result_known_response()

        return HttpResponse(
            json.dumps(result), content_type="application/json", status=200
        )


class SandboxView(View):
    def get(self, request, *args, **kwargs):

        base_path = os.path.dirname(__file__)
        get_fixture = lambda filename: open(
            os.path.join(base_path, "sandbox-responses", f"{filename}.json")
        )

        example_postcodes = (
            "AA11AA",  # no election
            "AA12AA",  # one election, station known, with candidates
            "AA12AB",  # one election, station not known, with candidates
            "AA13AA",  # address picker
            "AA14AA",  # multiple elections
            "AA15AA",  # Northern Ireland
        )

        if "postcode" in kwargs:
            postcode = re.sub("[^A-Z0-9]", "", kwargs["postcode"].upper())
            if postcode in example_postcodes:
                return HttpResponse(
                    get_fixture(postcode), content_type="application/json", status=200
                )
            return HttpResponse(
                json.dumps({"message": "Could not geocode from any source"}),
                content_type="application/json",
                status=400,
            )

        example_slugs = (
            "e09000033-2282254634585",
            "e09000033-8531289123599",
            "e09000033-7816246896787",
        )
        if "slug" in kwargs:
            if kwargs["slug"] in example_slugs:
                return HttpResponse(
                    get_fixture(kwargs["slug"]),
                    content_type="application/json",
                    status=200,
                )
            return HttpResponse(
                json.dumps({"message": "Address not found"}),
                content_type="application/json",
                status=404,
            )

        return HttpResponse(
            json.dumps({"message": "Internal Server Error"}),
            content_type="application/json",
            status=500,
        )
