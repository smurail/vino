import orjson

from django.http import HttpResponse
from django.views.generic.detail import BaseDetailView


class JsonResponse(HttpResponse):
    def __init__(self, data, safe=True, json_dumps_params=None, **kwargs):
        if safe and not isinstance(data, dict):
            raise TypeError(
                'In order to allow non-dict objects to be serialized set the '
                'safe parameter to False.'
            )
        if json_dumps_params is None:
            json_dumps_params = dict(
                option=orjson.OPT_NAIVE_UTC | orjson.OPT_SERIALIZE_NUMPY)
        kwargs.setdefault('content_type', 'application/json')
        data = orjson.dumps(data, **json_dumps_params)
        super().__init__(content=data, **kwargs)


class JsonResponseMixin:
    def render_to_json_response(self, context, **response_kwargs):
        return JsonResponse(self.get_data(context), **response_kwargs)

    def get_data(self, context):
        return context


class JsonDetailView(JsonResponseMixin, BaseDetailView):
    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)
