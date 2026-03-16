"""Graceful degradation service — applies strictest defaults when reasoning fails."""

import re
from datetime import date, timedelta

import structlog

from core.models.booking import BookingPlan, ReasoningResult

logger = structlog.get_logger()

_ROUTE_RE = re.compile(r"from\s+([A-Z]{3})\s+to\s+([A-Z]{3})", re.IGNORECASE)
_IATA_RE = re.compile(r"\b([A-Z]{3})\b")
_DATE_RE = re.compile(r"(?:on|for)\s+(\w+\s+\d{1,2}(?:\s*,?\s*\d{4})?)", re.IGNORECASE)


def _parse_query(user_query: str) -> tuple[str | None, str | None, date]:
    """Best-effort extraction of origin, destination, and date from user query.

    Returns (None, None, default_date) when airports cannot be identified.
    Airport codes are not PII — safe to log.
    """
    origin: str | None = None
    destination: str | None = None
    departure_date = date.today() + timedelta(days=30)

    route = _ROUTE_RE.search(user_query)
    if route:
        origin, destination = route.group(1).upper(), route.group(2).upper()
    else:
        codes = _IATA_RE.findall(user_query.upper())
        if len(codes) >= 2:
            origin, destination = codes[0], codes[1]

    date_match = _DATE_RE.search(user_query)
    if date_match:
        try:
            from dateutil.parser import parse as parse_date
            parsed = parse_date(date_match.group(1), fuzzy=True)
            if parsed.date() >= date.today():
                departure_date = parsed.date()
        except (ValueError, OverflowError, ImportError):
            pass

    return origin, destination, departure_date


def apply_graceful_degradation(
    booking_id: str,
    employee_id: str,
    user_query: str = "",
    error: str = "",
    cause: str = "",
) -> ReasoningResult:
    """Return a ReasoningResult built from strict defaults when reasoning has failed.

    If origin/destination can be parsed from the user query, the plan uses real
    airports and the workflow continues to flight search.
    If not, parse_failed=True signals the ASL to notify the user and end.
    """
    origin, destination, departure_date = _parse_query(user_query)
    parse_failed = origin is None or destination is None

    logger.warning(
        "graceful_degradation_applied",
        booking_id=booking_id,
        error=error,
        parsed_origin=origin,
        parsed_destination=destination,
        parse_failed=parse_failed,
    )

    warnings = ["STRICT_DEFAULTS_APPLIED"]
    if parse_failed:
        warnings.append("QUERY_PARSE_FAILED")
        # Build a dummy plan — it won't be used since parse_failed=True routes
        # to NotifyParseFailure in the ASL before reaching InvokeFlightSearch.
        plan = BookingPlan.strict_defaults(
            origin="DEL", destination="BOM", departure_date=departure_date
        ).model_copy(update={"warnings": warnings})
    else:
        plan = BookingPlan.strict_defaults(
            origin=origin,  # type: ignore[arg-type]
            destination=destination,  # type: ignore[arg-type]
            departure_date=departure_date,
        ).model_copy(update={"warnings": warnings})

    return ReasoningResult(
        booking_id=booking_id,
        employee_id=employee_id,
        plan=plan,
        model_id="strict-defaults",
        thinking_effort="medium",
        latency_ms=0.0,
        retry_count=0,
        escalated=False,
        parse_failed=parse_failed,
    )
