from http import HTTPStatus

from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc: Exception, context: dict) -> Response:
    """Custom API exception handler."""

    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        # Using the description's of the HTTPStatus class as error message.
        http_code_to_message = {v.value: v.description for v in HTTPStatus}

        error_payload = {
            "status_code": 0,
            "message": "",
            "details": [],
        }
        # error = error_payload["error"]
        status_code = response.status_code

        error_payload["status_code"] = status_code
        error_payload["message"] = http_code_to_message[status_code]
        error_payload["details"] = response.data
        response.data = error_payload
    return response
