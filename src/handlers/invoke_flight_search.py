"""Lambda handler — searches flights via dummy portal REST API."""

from typing import Any

from core.config import get_config
from core.services.flight_search_api import search_flights_via_api


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    config = get_config()
    return search_flights_via_api(event, config)
