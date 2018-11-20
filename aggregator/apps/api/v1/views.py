import abc
import asyncio
import aiohttp
import json
from django.http import HttpResponse
from django.views import View
from .api_client import ApiClient
from .stitcher import Stitcher, StitcherValidationError


class BaseView(View, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_response(self, request, *args, **kwargs):
        pass

    def get(self, request, *args, **kwargs):
        try:
            return self.get_response(request, *args, **kwargs)
        except aiohttp.ClientResponseError as e:
            # TODO: improve this
            return HttpResponse(
                json.dumps({"message": e.message}),
                content_type="application/json",
                status=e.status,
            )
        except asyncio.TimeoutError as e:
            # TODO: improve this
            return HttpResponse(
                json.dumps({"message": "timeout"}),
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
