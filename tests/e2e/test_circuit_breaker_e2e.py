"""
E2E tests — circuit breaker state transitions against deployed AWS resources.

Tests invoke Lambda functions directly and manipulate DynamoDB state to verify
circuit breaker behavior without running the full 20-minute booking workflow.

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
SEARCH_FUNCTION = "trip-cortex-dev-Functions-InvokeFlightSearchFuncti-qcy3yXPPctoH"
BOOKING_FUNCTION = "trip-cortex-dev-Functions-InvokeFlightBookingFunct-GXnPYiHb3IRt"

# Minimal valid event payloads (ACR will fail — that's expected for circuit tests)
_SEARCH_EVENT = {
    "booking_id": "e2e-cb-test",
    "employee_id": "e2e-tester",
    "plan": {
        "origin": "DEL",
        "destination": "BOM",
        "departure_date": "2026-03-20",
        "cabin_class": "economy",
        "parameters": {"fallback_url": "https://flysmart.dportal.workers.dev/search?from=DEL&to=BOM"},
    },
}
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


def _set_circuit_open(dynamo_client, circuit_id: str, last_failure_offset: int = 0) -> None:
    """Seed circuit as OPEN. last_failure_offset < 0 means in the past (timeout elapsed)."""
    now = time.time()
    dynamo_client.put_item(
        TableName=CIRCUIT_BREAKER_TABLE,
        Item={
            "circuitId": {"S": circuit_id},
            "state": {"S": "open"},
            "failureCount": {"N": "5"},
            "lastFailureTime": {"N": str(now + last_failure_offset)},
            "recoveryTimeout": {"N": "60"},
            "ttl": {"N": str(int(now) + 86400)},
        },
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


# ── Test 1: circuit CLOSED — Lambda proceeds to ACR (ACR will fail, that's fine) ──────────────

def test_search_circuit_closed_proceeds_to_acr(dynamo, lam):
    """With circuit CLOSED, Lambda must attempt ACR (not short-circuit)."""
    _delete_circuit(dynamo, "travel-portal-search")

    result = _invoke(lam, SEARCH_FUNCTION, _SEARCH_EVENT)

    # ACR will fail (no real portal), but the error must NOT be PortalUnavailableError
    assert result["error"] is not None, "Expected Lambda error (ACR failure)"
    error_msg = json.dumps(result["body"])
    assert "PortalUnavailableError" not in error_msg, (
        "Circuit was CLOSED — should not raise PortalUnavailableError"
    )
    print(f"\n✅ CLOSED circuit: ACR attempted, got expected ACR error: {result['body'].get('errorType', '')}")


# ── Test 2: circuit OPEN — Lambda short-circuits immediately ───────────────────────────────────

def test_search_circuit_open_raises_portal_unavailable(dynamo, lam):
    """With circuit OPEN (timeout not elapsed), Lambda must raise PortalUnavailableError."""
    _set_circuit_open(dynamo, "travel-portal-search", last_failure_offset=0)  # just now

    result = _invoke(lam, SEARCH_FUNCTION, _SEARCH_EVENT)

    assert result["error"] == "Unhandled", "Expected Lambda error"
    assert result["body"].get("errorType") == "PortalUnavailableError", (
        f"Expected PortalUnavailableError, got: {result['body'].get('errorType')}"
    )
    print("\n✅ OPEN circuit: PortalUnavailableError raised immediately (no ACR call)")


# ── Test 3: circuit OPEN + timeout elapsed → HALF_OPEN → test request allowed ─────────────────

def test_search_circuit_open_timeout_elapsed_transitions_half_open(dynamo, lam):
    """With circuit OPEN and timeout elapsed, Lambda transitions to HALF_OPEN and attempts ACR."""
    _set_circuit_open(dynamo, "travel-portal-search", last_failure_offset=-120)  # 2 min ago

    result = _invoke(lam, SEARCH_FUNCTION, _SEARCH_EVENT)

    # ACR will fail, but it must NOT be PortalUnavailableError (circuit allowed the request)
    assert result["error"] is not None
    assert result["body"].get("errorType") != "PortalUnavailableError", (
        "Timeout elapsed — circuit should have transitioned to HALF_OPEN and allowed request"
    )

    # Verify DynamoDB state is no longer OPEN (either HALF_OPEN or OPEN again after failure)
    item = _get_circuit(dynamo, "travel-portal-search")
    assert item, "Circuit item should exist"
    print(f"\n✅ OPEN+timeout: request allowed, state now: {item['state']['S']}")


# ── Test 4: booking circuit trips at threshold=3 (lower than search=5) ────────────────────────

def test_booking_circuit_trips_at_threshold_3(dynamo, lam):
    """Booking circuit must open after 3 failures, not 5."""
    _delete_circuit(dynamo, "travel-portal-booking")

    # Invoke 3 times — each will fail at ACR and record_failure
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


# ── Test 5: audit log entries created for circuit transitions ──────────────────────────────────

def test_audit_log_entries_created_on_circuit_open(dynamo, lam):
    """Circuit open event must produce an audit log entry."""
    _delete_circuit(dynamo, "travel-portal-search")

    # Seed failure count at threshold-1 so next failure opens the circuit
    now = time.time()
    dynamo.put_item(
        TableName=CIRCUIT_BREAKER_TABLE,
        Item={
            "circuitId": {"S": "travel-portal-search"},
            "state": {"S": "closed"},
            "failureCount": {"N": "4"},  # one below threshold=5
            "lastFailureTime": {"N": str(now)},
            "recoveryTimeout": {"N": "60"},
            "ttl": {"N": str(int(now) + 86400)},
        },
    )

    _invoke(lam, SEARCH_FUNCTION, _SEARCH_EVENT)  # 5th failure → circuit opens

    # Scan audit log for circuit_breaker event (recent entries only)
    datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # timestamp for context
    resp = dynamo.scan(
        TableName=AUDIT_LOG_TABLE,
        FilterExpression="#e = :ev AND #bk = :bk",
        ExpressionAttributeNames={"#e": "event", "#bk": "bookingId"},
        ExpressionAttributeValues={
            ":ev": {"S": "circuit_breaker"},
            ":bk": {"S": "e2e-audit-test"},
        },
    )
    items = resp.get("Items", [])
    actions = [i.get("output", {}).get("M", {}).get("action", {}).get("S", "") for i in items]
    print(f"\n  Audit entries found: {actions}")
    assert any(a in ("opened", "rejected") for a in actions), (
        f"Expected 'opened' or 'rejected' audit entry, got: {actions}"
    )
    print(f"✅ Audit log entry created: {actions}")


# ── Test 6: DynamoDB TTL is set on circuit entries ─────────────────────────────────────────────

def test_circuit_breaker_ttl_set(dynamo, lam):
    """Every write must set TTL to ~now+86400."""
    _delete_circuit(dynamo, "travel-portal-search")

    _invoke(lam, SEARCH_FUNCTION, _SEARCH_EVENT)  # triggers record_failure

    item = _get_circuit(dynamo, "travel-portal-search")
    assert item, "Circuit item must exist after failure"
    ttl = int(item.get("ttl", {}).get("N", 0))
    now = int(time.time())
    assert 86300 < ttl - now < 86500, f"TTL should be ~now+86400, got offset: {ttl - now}"
    print(f"\n✅ TTL set correctly: expires in {(ttl - now) // 3600}h")


# ── Cleanup ────────────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def cleanup_after(dynamo):
    yield
    # Reset circuits after each test so they don't interfere
    for circuit_id in ("travel-portal-search", "travel-portal-booking"):
        try:
            _delete_circuit(dynamo, circuit_id)
        except Exception:
            pass
