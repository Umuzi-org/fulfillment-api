import time

from django.db import Error as DatabaseError
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

STARTED_AT = time.monotonic()


@require_GET
def health(request):
    database = "ok"
    status_code = 200
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        database = "unavailable"
        status_code = 503

    return JsonResponse(
        {
            "status": "ok" if database == "ok" else "unavailable",
            "database": database,
            "uptime_seconds": int(time.monotonic() - STARTED_AT),
        },
        status=status_code,
    )
