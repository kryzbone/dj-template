from rest_framework.renderers import JSONRenderer


class CustomRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        status_code = renderer_context["response"].status_code
        response = {"data": data, "error": None}

        if not str(status_code).startswith("2"):
            response["error"] = data
            response["data"] = None

        return super(CustomRenderer, self).render(
            response, accepted_media_type, renderer_context
        )
