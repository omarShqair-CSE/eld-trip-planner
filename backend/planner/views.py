from datetime import datetime

import requests
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from .serializers import TripSerializer
from .services.geo import GeoError
from .services.trip import build_plan


def _parse_start(value):
    """Naive local time at the home terminal (HOS uses the home-terminal clock)."""
    if value:
        try:
            return datetime.fromisoformat(value).replace(tzinfo=None)
        except ValueError:
            pass
    return datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
def health(request):
    return Response({"status": "ok"})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def plan(request):
    ser = TripSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data
    try:
        result = build_plan(
            d["current_location"], d["pickup_location"], d["dropoff_location"],
            d["cycle_used"], _parse_start(d.get("start_time")),
        )
    except GeoError as exc:
        return Response({"error": str(exc)}, status=400)
    except requests.RequestException:
        return Response({"error": "The map service is busy. Please try again in a moment."}, status=502)
    return Response(result)