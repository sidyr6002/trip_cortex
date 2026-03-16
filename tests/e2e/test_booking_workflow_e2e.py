"""
E2E test — full booking workflow via Step Functions direct invocation.

Bypasses WebSocket/JWT entirely. Tests the real pipeline:
  EmbedAndRetrieve → ReasonAndPlan → ValidatePlan
  → InvokeFlightSearch → SendFlightOptions (HITL) → InvokeFlightBooking → NotifyBookingComplete

Usage:
    PYTHONPATH=src uv run pytest tests/e2e/test_booking_workflow_e2e.py -v -s
"""

import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import boto3
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.services.task_token import pop_task_token  # noqa: E402

REGION = "us-east-1"
STATE_MACHINE_ARN = "arn:aws:states:us-east-1:591618107284:stateMachine:trip-cortex-dev-booking-workflow"
BOOKINGS_TABLE = "trip-cortex-dev-bookings"
POLL_INTERVAL_S = 15
TIMEOUT_S = 600  # 10 min — ReasonAndPlan (~8 min) + portal API search (instant) + buffer
HITL_TIMEOUT_S = TIMEOUT_S - 60

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def sfn():
    return boto3.client("stepfunctions", region_name=REGION)


@pytest.fixture(scope="module")
def dynamo():
    return boto3.client("dynamodb", region_name=REGION)


def _start_execution(sfn_client, query: str, employee_id: str, booking_id: str) -> str:
    resp = sfn_client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=booking_id,
        input=json.dumps({
            "employee_id": employee_id,
            "booking_id": booking_id,
            "connection_id": "e2e-mock-connection",  # ResponseSender fails gracefully — no real WS
            "query": query,
        }),
    )
    return resp["executionArn"]


def _poll_until_done(sfn_client, execution_arn: str) -> dict:
    deadline = time.monotonic() + TIMEOUT_S
    while time.monotonic() < deadline:
        resp = sfn_client.describe_execution(executionArn=execution_arn)
        status = resp["status"]
        if status in ("SUCCEEDED", "FAILED", "TIMED_OUT", "ABORTED"):
            return resp
        print(f"  [{time.strftime('%H:%M:%S')}] {status} — next poll in {POLL_INTERVAL_S}s...")
        time.sleep(POLL_INTERVAL_S)
    raise TimeoutError(f"Execution did not complete within {TIMEOUT_S}s")


def _get_flight_options_from_history(sfn_client, execution_arn: str) -> list:
    """Extract flight options from InvokeFlightSearch output in execution history."""
    history = sfn_client.get_execution_history(executionArn=execution_arn, maxResults=1000)
    for event in reversed(history["events"]):
        if event["type"] == "TaskStateExited":
            details = event.get("stateExitedEventDetails", {})
            if details.get("name") == "InvokeFlightSearch":
                output = json.loads(details.get("output", "{}"))
                return output.get("search_result", {}).get("flights", [])
    return []


def _resolve_hitl(sfn_client, dynamo_client, booking_id: str, employee_id: str,
                  execution_arn: str, stop_event: threading.Event) -> None:
    """Poll DynamoDB for task token, then SendTaskSuccess with cheapest flight."""
    deadline = time.monotonic() + HITL_TIMEOUT_S
    while time.monotonic() < deadline and not stop_event.is_set():
        try:
            task_token = pop_task_token(dynamo_client, BOOKINGS_TABLE, booking_id, employee_id)
        except KeyError:
            time.sleep(10)
            continue

        # Get actual flights from search result
        flights = _get_flight_options_from_history(sfn_client, execution_arn)
        if not flights:
            # Fallback: use a known DEL→BOM flight if search returned nothing
            print("  HITL: no flights in history, using fallback flight")
            flight = {"airline": "Vistara", "flight_number": "UK-933", "price": 98.0,
                      "departure_time": "09:00", "arrival_time": "11:10",
                      "stops": 0, "cabin_class": "Economy", "duration": "2h 10m"}
        else:
            flight = min(flights, key=lambda f: f["price"])

        print(f"  HITL: selecting {flight['airline']} {flight['flight_number']} ${flight['price']}")
        sfn_client.send_task_success(
            taskToken=task_token,
            output=json.dumps({
                "flight": flight,
                "passengers": [{
                    "first_name": "E2E", "last_name": "Tester",
                    "date_of_birth": "01-01-1990",
                    "email": "e2e@example.com",
                    "phone": "+91 9999999999",
                }],
                "search_url": "https://flysmart.dportal.workers.dev/search?from=DEL&to=BOM&date=2026-03-20&class=economy",
            }),
        )
        print("  HITL resolved ✅")
        return

    print("  HITL: task token not found within timeout — workflow may have taken fallback path")


def test_full_booking_workflow_del_to_bom(sfn, dynamo):
    """Full pipeline: DEL→BOM economy, policy retrieval, flight search, HITL, booking."""
    booking_id = f"e2e-{int(time.time())}"
    employee_id = "e2e-test-user"

    execution_arn = _start_execution(sfn, "Book a flight from DEL to BOM on March 20 2026 economy class",
                                     employee_id, booking_id)
    print(f"\nStarted: {execution_arn}")

    stop_event = threading.Event()
    hitl_thread = threading.Thread(
        target=_resolve_hitl,
        args=(sfn, dynamo, booking_id, employee_id, execution_arn, stop_event),
        daemon=True,
    )
    hitl_thread.start()

    try:
        result = _poll_until_done(sfn, execution_arn)
    finally:
        stop_event.set()
        hitl_thread.join(timeout=5)

    print(f"\nFinal status: {result['status']}")
    assert result["status"] == "SUCCEEDED", f"Execution failed: {result.get('cause', '')}"

    output = json.loads(result["output"])
    booking_result = output.get("booking_result", {})
    print(f"Booking result: {json.dumps(booking_result, indent=2, default=str)}")

    # ── Core identity ────────────────────────────────────────────────────────
    assert booking_result, "No booking_result in output"
    assert booking_result.get("booking_id") == booking_id
    assert booking_result.get("employee_id") == employee_id

    # ── Outcome: confirmed booking (happy path) ──────────────────────────────
    confirmation = booking_result.get("confirmation")
    fallback_url = booking_result.get("fallback_url")

    if confirmation:
        assert confirmation.get("booking_reference"), "booking_reference missing"
        assert confirmation.get("payment_reference"), "payment_reference missing"
        assert isinstance(confirmation.get("total_amount"), (int, float)), "total_amount must be numeric"
        assert confirmation["total_amount"] > 0, "total_amount must be positive"
        assert confirmation.get("flight_number") == "SG-8194", (
            f"Expected cheapest flight SG-8194, got {confirmation.get('flight_number')}"
        )
        print(f"\n✅ Confirmed: {confirmation['booking_reference']} — ${confirmation['total_amount']}")
    else:
        # Graceful fallback is acceptable but worth flagging
        assert fallback_url, "Expected either confirmation or fallback_url"
        print(f"\n⚠️  Fallback URL returned: {fallback_url}")

    # ── Flight search produced real results ──────────────────────────────────
    flights = _get_flight_options_from_history(sfn, execution_arn)
    assert len(flights) > 0, "Flight search returned no results"
    assert any(f["flight_number"] == "SG-8194" for f in flights), (
        "Expected SpiceJet SG-8194 in search results"
    )

    # ── Selected flight matches what HITL sent ───────────────────────────────
    selected = output.get("selected_flight", {}).get("flight", {})
    assert selected.get("flight_number") == "SG-8194", (
        f"HITL should have selected cheapest SG-8194, got {selected.get('flight_number')}"
    )


BOOKING_REQUEST_FUNCTION = "trip-cortex-dev-FunctionsSt-BookingRequestFunction-SW7VHPFLIF2h"
HEARTBEAT_FUNCTION = "trip-cortex-dev-FunctionsStack-1-HeartbeatFunction-h7BFAwLMt9sb"


@pytest.fixture(scope="module")
def lambda_client():
    return boto3.client("lambda", region_name=REGION)


def _invoke_booking_request(lambda_client, employee_id: str, booking_id: str) -> dict:
    """Invoke BookingRequestFunction directly with a synthetic WebSocket event."""
    event = {
        "requestContext": {"connectionId": "e2e-guard-conn"},
        "body": json.dumps({
            "employee_id": employee_id,
            "booking_id": booking_id,
            "user_query": "Book a flight from DEL to BOM on March 20 2026 economy class",
        }),
    }
    resp = lambda_client.invoke(
        FunctionName=BOOKING_REQUEST_FUNCTION,
        InvocationType="RequestResponse",
        Payload=json.dumps(event).encode(),
    )
    return json.loads(resp["Payload"].read())


def _cleanup_booking(dynamo_client, employee_id: str, booking_id: str) -> None:
    dynamo_client.delete_item(
        TableName=BOOKINGS_TABLE,
        Key={"employeeId": {"S": employee_id}, "bookingId": {"S": booking_id}},
    )


def test_single_active_booking_guard_e2e(sfn, dynamo, lambda_client):
    """Second booking request for same employee is rejected with 409 while first is ACTIVE."""
    employee_id = "e2e-guard-test"
    booking_id_1 = f"e2e-guard-{int(time.time())}-1"
    booking_id_2 = f"e2e-guard-{int(time.time())}-2"

    try:
        # First request — should succeed
        resp1 = _invoke_booking_request(lambda_client, employee_id, booking_id_1)
        assert resp1["statusCode"] == 200, f"First request failed: {resp1}"

        # Second request immediately after — should be rejected
        resp2 = _invoke_booking_request(lambda_client, employee_id, booking_id_2)
        assert resp2["statusCode"] == 409, f"Expected 409, got: {resp2}"

        # Exactly 1 ACTIVE record in DynamoDB
        active = dynamo.query(
            TableName=BOOKINGS_TABLE,
            KeyConditionExpression="employeeId = :e",
            FilterExpression="#s = :active",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":e": {"S": employee_id}, ":active": {"S": "ACTIVE"}},
        )
        assert active["Count"] == 1, f"Expected 1 ACTIVE record, got {active['Count']}"

    finally:
        # Stop the execution and clean up
        active_items = dynamo.query(
            TableName=BOOKINGS_TABLE,
            KeyConditionExpression="employeeId = :e",
            ExpressionAttributeValues={":e": {"S": employee_id}},
        ).get("Items", [])
        for item in active_items:
            exec_arn = item.get("executionArn", {}).get("S", "")
            if exec_arn:
                try:
                    sfn.stop_execution(executionArn=exec_arn, cause="e2e cleanup")
                except Exception:
                    pass
            _cleanup_booking(dynamo, employee_id, item["bookingId"]["S"])


def test_booking_record_lifecycle_e2e(sfn, dynamo):
    """After a completed workflow, booking record has status=COMPLETED, completedAt, executionArn."""
    # Find the most recent COMPLETED booking for the e2e test user
    resp = dynamo.query(
        TableName=BOOKINGS_TABLE,
        KeyConditionExpression="employeeId = :e",
        FilterExpression="#s = :completed",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":e": {"S": "e2e-test-user"}, ":completed": {"S": "COMPLETED"}},
    )
    assert resp["Count"] > 0, (
        "No COMPLETED booking found for e2e-test-user — run test_full_booking_workflow_del_to_bom first"
    )

    item = resp["Items"][0]
    assert item["status"]["S"] == "COMPLETED"
    assert "completedAt" in item, "completedAt not set"
    # Validate ISO timestamp
    datetime.fromisoformat(item["completedAt"]["S"])


def test_stale_booking_cleanup_e2e(dynamo, lambda_client):
    """Heartbeat marks ACTIVE bookings older than 2 hours as FAILED."""
    from datetime import datetime, timedelta, timezone

    employee_id = "e2e-stale-test"
    booking_id = f"e2e-stale-{int(time.time())}"
    stale_created_at = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()

    # Insert a stale ACTIVE record with a non-existent executionArn
    dynamo.put_item(
        TableName=BOOKINGS_TABLE,
        Item={
            "employeeId": {"S": employee_id},
            "bookingId": {"S": booking_id},
            "status": {"S": "ACTIVE"},
            "connectionId": {"S": "e2e-stale-conn"},
            "executionArn": {"S": "arn:aws:states:us-east-1:000000000000:execution:nonexistent:nonexistent"},
            "createdAt": {"S": stale_created_at},
        },
    )

    try:
        # Invoke heartbeat directly
        resp = lambda_client.invoke(
            FunctionName=HEARTBEAT_FUNCTION,
            InvocationType="RequestResponse",
            Payload=b"{}",
        )
        result = json.loads(resp["Payload"].read())
        assert result["statusCode"] == 200

        # Booking should now be FAILED
        item_resp = dynamo.get_item(
            TableName=BOOKINGS_TABLE,
            Key={"employeeId": {"S": employee_id}, "bookingId": {"S": booking_id}},
        )
        item = item_resp.get("Item", {})
        assert item.get("status", {}).get("S") == "FAILED", (
            f"Expected FAILED, got {item.get('status', {}).get('S')}"
        )
        assert "completedAt" in item

    finally:
        _cleanup_booking(dynamo, employee_id, booking_id)
