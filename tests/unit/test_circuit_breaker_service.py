"""Unit tests for CircuitBreakerService — mocked DynamoDB, no AWS calls."""

from unittest.mock import MagicMock, call, patch

import pytest

from core.models.circuit_breaker import CircuitBreakerState, CircuitState
from core.services.circuit_breaker import CircuitBreakerService

TABLE = "TripCortexCircuitBreaker"
CIRCUIT_ID = "travel-portal-search"


def _make_dynamo_item(
    state: str = "closed",
    failure_count: int = 0,
    last_failure_time: float = 0.0,
    recovery_timeout: int = 60,
) -> dict:
    return {
        "circuitId": {"S": CIRCUIT_ID},
        "state": {"S": state},
        "failureCount": {"N": str(failure_count)},
        "lastFailureTime": {"N": str(last_failure_time)},
        "recoveryTimeout": {"N": str(recovery_timeout)},
        "ttl": {"N": "9999999999"},
    }


@pytest.fixture
def dynamo() -> MagicMock:
    client = MagicMock()
    # Default: item not found
    client.get_item.return_value = {}
    # Default: update_item returns empty attributes
    client.update_item.return_value = {"Attributes": {"failureCount": {"N": "1"}}}
    # Wire ConditionalCheckFailedException
    client.exceptions.ConditionalCheckFailedException = Exception
    return client


@pytest.fixture
def svc(dynamo: MagicMock) -> CircuitBreakerService:
    return CircuitBreakerService(dynamo, TABLE, failure_threshold=5, recovery_timeout=60)


# ── get_state ────────────────────────────────────────────────────────────────


def test_get_state_no_item_returns_closed(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    state = svc.get_state(CIRCUIT_ID)
    assert state.state == CircuitState.CLOSED
    assert state.failure_count == 0


def test_get_state_parses_dynamo_item(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    dynamo.get_item.return_value = {"Item": _make_dynamo_item("open", 5, 1000.0)}
    state = svc.get_state(CIRCUIT_ID)
    assert state.state == CircuitState.OPEN
    assert state.failure_count == 5
    assert state.last_failure_time == 1000.0


# ── can_execute ──────────────────────────────────────────────────────────────


def test_can_execute_closed_returns_true(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    dynamo.get_item.return_value = {"Item": _make_dynamo_item("closed")}
    assert svc.can_execute(CIRCUIT_ID) is True


def test_can_execute_half_open_returns_true(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    dynamo.get_item.return_value = {"Item": _make_dynamo_item("half_open")}
    assert svc.can_execute(CIRCUIT_ID) is True


def test_can_execute_open_before_timeout_returns_false(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    with patch("core.services.circuit_breaker.time.time", return_value=1000.0):
        dynamo.get_item.return_value = {"Item": _make_dynamo_item("open", last_failure_time=990.0)}
        assert svc.can_execute(CIRCUIT_ID) is False
        dynamo.update_item.assert_not_called()


def test_can_execute_open_after_timeout_transitions_half_open(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    with patch("core.services.circuit_breaker.time.time", return_value=2000.0):
        dynamo.get_item.return_value = {"Item": _make_dynamo_item("open", last_failure_time=1000.0)}
        result = svc.can_execute(CIRCUIT_ID)
    assert result is True
    dynamo.update_item.assert_called_once()
    call_kwargs = dynamo.update_item.call_args[1]
    assert ":half_open" in call_kwargs["ExpressionAttributeValues"]


def test_can_execute_open_after_timeout_race_condition(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    """Another Lambda already transitioned — ConditionalCheckFailedException → False."""
    dynamo.update_item.side_effect = dynamo.exceptions.ConditionalCheckFailedException("race")
    with patch("core.services.circuit_breaker.time.time", return_value=2000.0):
        dynamo.get_item.return_value = {"Item": _make_dynamo_item("open", last_failure_time=1000.0)}
        assert svc.can_execute(CIRCUIT_ID) is False


# ── record_failure ───────────────────────────────────────────────────────────


def test_record_failure_increments_count(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    dynamo.update_item.return_value = {"Attributes": {"failureCount": {"N": "1"}}}
    dynamo.get_item.return_value = {"Item": _make_dynamo_item("closed", 1)}
    svc.record_failure(CIRCUIT_ID)
    first_call = dynamo.update_item.call_args_list[0]
    assert "ADD failureCount :one" in first_call[1]["UpdateExpression"]


def test_record_failure_below_threshold_stays_closed(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    dynamo.update_item.return_value = {"Attributes": {"failureCount": {"N": "3"}}}
    dynamo.get_item.return_value = {"Item": _make_dynamo_item("closed", 3)}
    svc.record_failure(CIRCUIT_ID)
    # Only one update_item call (the ADD) — no state transition call
    assert dynamo.update_item.call_count == 1


def test_record_failure_opens_circuit_at_threshold(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    dynamo.update_item.return_value = {"Attributes": {"failureCount": {"N": "5"}}}
    dynamo.get_item.return_value = {"Item": _make_dynamo_item("open", 5)}
    svc.record_failure(CIRCUIT_ID)
    # Two update_item calls: ADD increment + state transition to OPEN
    assert dynamo.update_item.call_count == 2
    second_call = dynamo.update_item.call_args_list[1]
    assert ":open" in second_call[1]["ExpressionAttributeValues"]


def test_record_failure_already_open_is_idempotent(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    """Second update_item (state flip) raises ConditionalCheckFailedException — must not propagate."""
    dynamo.update_item.side_effect = [
        {"Attributes": {"failureCount": {"N": "6"}}},  # ADD succeeds
        dynamo.exceptions.ConditionalCheckFailedException("already open"),  # flip fails
    ]
    dynamo.get_item.return_value = {"Item": _make_dynamo_item("open", 6)}
    svc.record_failure(CIRCUIT_ID)  # must not raise


# ── record_success ───────────────────────────────────────────────────────────


def test_record_success_resets_to_closed(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    dynamo.get_item.return_value = {"Item": _make_dynamo_item("closed", 0)}
    svc.record_success(CIRCUIT_ID)
    call_kwargs = dynamo.update_item.call_args[1]
    assert ":closed" in call_kwargs["ExpressionAttributeValues"]
    assert ":zero" in call_kwargs["ExpressionAttributeValues"]


def test_record_success_from_half_open(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    dynamo.get_item.return_value = {"Item": _make_dynamo_item("closed", 0)}
    svc.record_success(CIRCUIT_ID)
    call_kwargs = dynamo.update_item.call_args[1]
    assert call_kwargs["ExpressionAttributeValues"][":closed"]["S"] == "closed"


# ── TTL ──────────────────────────────────────────────────────────────────────


def test_ttl_set_on_record_failure(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    with patch("core.services.circuit_breaker.time.time", return_value=1000.0):
        dynamo.update_item.return_value = {"Attributes": {"failureCount": {"N": "1"}}}
        dynamo.get_item.return_value = {"Item": _make_dynamo_item("closed", 1)}
        svc.record_failure(CIRCUIT_ID)
    first_call = dynamo.update_item.call_args_list[0]
    ttl_val = first_call[1]["ExpressionAttributeValues"][":ttl"]["N"]
    assert ttl_val == str(1000 + 86400)


def test_ttl_set_on_record_success(svc: CircuitBreakerService, dynamo: MagicMock) -> None:
    with patch("core.services.circuit_breaker.time.time", return_value=1000.0):
        dynamo.get_item.return_value = {"Item": _make_dynamo_item("closed", 0)}
        svc.record_success(CIRCUIT_ID)
    call_kwargs = dynamo.update_item.call_args[1]
    ttl_val = call_kwargs["ExpressionAttributeValues"][":ttl"]["N"]
    assert ttl_val == str(1000 + 86400)
