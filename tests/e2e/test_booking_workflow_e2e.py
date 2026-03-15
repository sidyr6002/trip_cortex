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
import time
import threading
from pathlib import Path

import boto3
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.services.task_token import pop_task_token  # noqa: E402

REGION = "us-east-1"
STATE_MACHINE_ARN = "arn:aws:states:us-east-1:591618107284:stateMachine:trip-cortex-dev-booking-workflow"
BOOKINGS_TABLE = "trip-cortex-dev-bookings"
POLL_INTERVAL_S = 15
TIMEOUT_S = 900  # 15 min — ReasonAndPlan (~5 min) + 2x ACR (~4 min each)

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
    history = sfn_client.get_execution_history(executionArn=execution_arn, maxResults=100)
    for event in reversed(history["events"]):
        if event["type"] == "TaskStateExited":
            details = event.get("stateExitedEventDetails", {})
            if details.get("name") == "InvokeFlightSearch":
                output = json.loads(details.get("output", "{}"))
                return output.get("flight_search_result", {}).get("search_result", {}).get("flights", [])
    return []


def _resolve_hitl(sfn_client, dynamo_client, booking_id: str, employee_id: str,
                  execution_arn: str, stop_event: threading.Event) -> None:
    """Poll DynamoDB for task token, then SendTaskSuccess with cheapest flight."""
    deadline = time.monotonic() + 360  # 6 min to find HITL
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
            flight = {"airline": "SpiceJet", "flight_number": "SG-8194", "price": 72.0,
                      "departure_time": "17:00", "arrival_time": "19:15",
                      "stops": 0, "cabin_class": "Economy", "duration": "2h 15m"}
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

    assert booking_result, "No booking_result in output"
    assert booking_result.get("booking_id") == booking_id
    # Either confirmed booking or graceful fallback — both are valid
    has_confirmation = booking_result.get("confirmation") is not None
    has_fallback = booking_result.get("fallback_url") is not None
    assert has_confirmation or has_fallback, "Expected either confirmation or fallback_url"
    print(f"\n{'✅ Confirmed booking' if has_confirmation else '⚠️  Fallback URL returned'}")
