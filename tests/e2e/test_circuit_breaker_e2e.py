"""
E2E tests — circuit breaker state transitions for the booking ACR workflow.

Search no longer uses ACR (replaced by portal REST API), so only booking
circuit breaker tests remain.

Usage:
    uv run pytest tests/e2e/test_circuit_breaker_e2e.py -v -s -m e2e
"""

import json
import time
from datetime import datetime, timezone

import boto3
import pytest

REGION = "us-east-1"
CIRCUIT_BREAKER_TABLE = "trip-cortex-dev-circuit-breaker"
AUDIT_LOG_TABLE = "trip-cortex-dev-audit-log"
BOOKING_FUNCTION = "trip-cortex-dev-Functions-InvokeFlightBookingFunct-GXnPYiHb3IRt"

_BOOKING_EVENT = {
    "booking_id": "e2e-cb-test",
    "employee_id": "e2e-tester",
    "validated_result": {
        "plan": {
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": "2026-03-20",
            "cabin_class": "economy",
            "parameters": {"fallback_url": "https://flysmart.dportal.workers.dev/search?from=DEL&to=BOM"},
        }
    },
    "selected_flight": {
        "flight": {"flight_number": "SG-8194", "price": 98.0},
        "passengers": [{"first_name": "E2E", "last_name": "Tester"}],
        "search_url": "https://flysmart.dportal.workers.dev/search?from=DEL&to=BOM",
    },
}

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def dynamo():
    return boto3.client("dynamodb", region_name=REGION)


@pytest.fixture(scope="module")
def lam():
    return boto3.client("lambda", region_name=REGION)


def _delete_circuit(dynamo_client, circuit_id: str) -> None:
    dynamo_client.delete_item(
        TableName=CIRCUIT_BREAKER_TABLE,
        Key={"circuitId": {"S": circuit_id}},
    )


def _get_circuit(dynamo_client, circuit_id: str) -> dict:
    resp = dynamo_client.get_item(
        TableName=CIRCUIT_BREAKER_TABLE,
        Key={"circuitId": {"S": circuit_id}},
    )
    return resp.get("Item", {})


def _invoke(lam_client, function_name: str, payload: dict) -> dict:
    resp = lam_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode(),
    )
    body = json.loads(resp["Payload"].read())
    return {"status_code": resp["StatusCode"], "body": body, "error": resp.get("FunctionError")}


# ── Test 1: booking circuit trips at threshold=3 ──────────────────────────────

def test_booking_circuit_trips_at_threshold_3(dynamo, lam):
    """Booking circuit must open after 3 failures."""
    _delete_circuit(dynamo, "travel-portal-booking")

    for i in range(3):
        _invoke(lam, BOOKING_FUNCTION, _BOOKING_EVENT)
        item = _get_circuit(dynamo, "travel-portal-booking")
        count = int(item.get("failureCount", {}).get("N", 0)) if item else 0
        state = item.get("state", {}).get("S", "closed") if item else "closed"
        print(f"  After failure {i+1}: count={count}, state={state}")

    item = _get_circuit(dynamo, "travel-portal-booking")
    assert item.get("state", {}).get("S") == "open", (
        f"Booking circuit should be OPEN after 3 failures, got: {item.get('state', {}).get('S')}"
    )
    print("\n✅ Booking circuit opened at threshold=3")

    # 4th invocation must be PortalUnavailableError
    result = _invoke(lam, BOOKING_FUNCTION, _BOOKING_EVENT)
    assert result["body"].get("errorType") == "PortalUnavailableError", (
        f"4th booking request should be blocked, got: {result['body'].get('errorType')}"
    )
    print("✅ 4th booking request blocked by open circuit")


# ── Test 2: booking circuit OPEN + timeout elapsed → allows request ───────────

def test_booking_circuit_open_timeout_elapsed_allows_request(dynamo, lam):
    """With circuit OPEN and timeout elapsed, booking Lambda transitions to HALF_OPEN."""
    now = time.time()
    dynamo.put_item(
        TableName=CIRCUIT_BREAKER_TABLE,
        Item={
            "circuitId": {"S": "travel-portal-booking"},
            "state": {"S": "open"},
            "failureCount": {"N": "3"},
            "lastFailureTime": {"N": str(now - 120)},  # 2 min ago — timeout elapsed
            "recoveryTimeout": {"N": "60"},
            "ttl": {"N": str(int(now) + 86400)},
        },
    )

    result = _invoke(lam, BOOKING_FUNCTION, _BOOKING_EVENT)

    # ACR will fail, but must NOT be PortalUnavailableError (circuit allowed the request)
    assert result["error"] is not None
    assert result["body"].get("errorType") != "PortalUnavailableError", (
        "Timeout elapsed — circuit should have transitioned to HALF_OPEN and allowed request"
    )
    item = _get_circuit(dynamo, "travel-portal-booking")
    print(f"\n✅ OPEN+timeout: request allowed, state now: {item.get('state', {}).get('S')}")


# ── Test 3: TTL is set on circuit entries ─────────────────────────────────────

def test_booking_circuit_breaker_ttl_set(dynamo, lam):
    """Every write must set TTL to ~now+86400."""
    _delete_circuit(dynamo, "travel-portal-booking")

    _invoke(lam, BOOKING_FUNCTION, _BOOKING_EVENT)

    item = _get_circuit(dynamo, "travel-portal-booking")
    assert item, "Circuit item must exist after failure"
    ttl = int(item.get("ttl", {}).get("N", 0))
    now = int(time.time())
    assert 86300 < ttl - now < 86500, f"TTL should be ~now+86400, got offset: {ttl - now}"
    print(f"\n✅ TTL set correctly: expires in {(ttl - now) // 3600}h")


# ── Test 4: audit log entry created on circuit open ───────────────────────────

def test_audit_log_entry_created_on_booking_circuit_open(dynamo, lam):
    """Circuit open event must produce an audit log entry."""
    _delete_circuit(dynamo, "travel-portal-booking")

    now = time.time()
    dynamo.put_item(
        TableName=CIRCUIT_BREAKER_TABLE,
        Item={
            "circuitId": {"S": "travel-portal-booking"},
            "state": {"S": "closed"},
            "failureCount": {"N": "2"},  # one below threshold=3
            "lastFailureTime": {"N": str(now)},
            "recoveryTimeout": {"N": "60"},
            "ttl": {"N": str(int(now) + 86400)},
        },
    )

    _invoke(lam, BOOKING_FUNCTION, _BOOKING_EVENT)  # 3rd failure → circuit opens

    resp = dynamo.scan(
        TableName=AUDIT_LOG_TABLE,
        FilterExpression="#e = :ev AND #bk = :bk",
        ExpressionAttributeNames={"#e": "event", "#bk": "bookingId"},
        ExpressionAttributeValues={
            ":ev": {"S": "circuit_breaker"},
            ":bk": {"S": "e2e-cb-test"},
        },
    )
    items = resp.get("Items", [])
    actions = [i.get("output", {}).get("M", {}).get("action", {}).get("S", "") for i in items]
    assert any(a in ("opened", "rejected") for a in actions), (
        f"Expected 'opened' or 'rejected' audit entry, got: {actions}"
    )
    print(f"\n✅ Audit log entry created: {actions}")


# ── Cleanup ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def cleanup_after(dynamo):
    yield
    try:
        _delete_circuit(dynamo, "travel-portal-booking")
    except Exception:
        pass
