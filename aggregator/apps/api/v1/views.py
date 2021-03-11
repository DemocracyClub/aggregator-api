import abc
import asyncio
import aiohttp
import os
import re
from django.http import HttpResponse, JsonResponse
from django.views import View
from ..errors import ApiError
from .api_client import EEApiClient, WdivWcivfApiClient, UpstreamApiError
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
            raise ApiError("Invalid token.", status=401)

        try:
            return self.get_response(request, *args, **kwargs)
        except UpstreamApiError as e:
            raise ApiError(e.message, status=e.status)
        except (asyncio.TimeoutError, aiohttp.ClientConnectorError):
            raise ApiError("Backend Connection Error")


class PostcodeView(BaseView):
    def get_response(self, request, *args, **kwargs):
        client = WdivWcivfApiClient(request)
        wdiv, wcivf = client.get_data_for_postcode(kwargs["postcode"])

        try:
            stitcher = Stitcher(wdiv, wcivf, request)
        except StitcherValidationError:
            raise ApiError("Internal Server Error")

        if not wdiv["polling_station_known"] and len(wdiv["addresses"]) > 0:
            result = stitcher.make_address_picker_response()
        else:
            result = stitcher.make_result_known_response()

        return JsonResponse(result, status=200)


class AddressView(BaseView):
    def get_response(self, request, *args, **kwargs):
        client = WdivWcivfApiClient(request)
        wdiv, wcivf = client.get_data_for_address(kwargs["slug"])

        try:
            stitcher = Stitcher(wdiv, wcivf, request)
        except StitcherValidationError:
            raise ApiError("Internal Server Error")

        result = stitcher.make_result_known_response()

        return JsonResponse(result, status=200)


class ElectionListView(BaseView):
    def get_response(self, request, *args, **kwargs):
        client = EEApiClient(request)
        result = client.get_election_list(request.GET)
        return JsonResponse(result, status=200)


class SingleElectionView(BaseView):
    def get_response(self, request, *args, **kwargs):
        client = EEApiClient(request)
        result = client.get_single_election(kwargs["slug"])
        return JsonResponse(result, status=200)


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
            "EH11YJ",  # Scotland, different registration address
        )

        if "postcode" in kwargs:
            postcode = re.sub("[^A-Z0-9]", "", kwargs["postcode"].upper())
            if postcode in example_postcodes:
                return HttpResponse(
                    get_fixture(postcode), content_type="application/json", status=200
                )
            raise ApiError("Could not geocode from any source", status=400)

        example_slugs = ("10035187881", "10035187882", "10035187883")
        if "slug" in kwargs:
            if kwargs["slug"] in example_slugs:
                return HttpResponse(
                    get_fixture(kwargs["slug"]),
                    content_type="application/json",
                    status=200,
                )
            raise ApiError("Address not found", status=404)

        raise ApiError("Internal Server Error")
