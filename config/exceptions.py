from django.http import Http404, JsonResponse
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def error_payload(code, message, details=None):
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }


def _plain(value):
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return str(value)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    if isinstance(exc, ValidationError):
        code = "validation_error"
        message = "Invalid input."
        details = (
            _plain(data) if isinstance(data, dict)
            else {"non_field_errors": _plain(data)}
        )
    elif isinstance(exc, Http404):
        code = "not_found"
        message = (
            str(data["detail"])
            if isinstance(data, dict) and "detail" in data
            else "Not found."
        )
        details = {}
    elif isinstance(data, dict) and "detail" in data:
        code = getattr(exc, "default_code", "error")
        message = str(data["detail"])
        details = {
            key: _plain(value)
            for key, value in data.items()
            if key != "detail"
        }
    else:
        code = getattr(exc, "default_code", "error")
        message = "Request failed."
        details = _plain(data) if isinstance(data, dict) else {}

    response.data = error_payload(code, message, details)
    return response


def not_found(request, exception=None, **kwargs):
    return JsonResponse(
        error_payload("not_found", "Not found."),
        status=404,
    )


def server_error(request):
    return JsonResponse(
        error_payload("server_error", "Something went wrong."),
        status=500,
    )
