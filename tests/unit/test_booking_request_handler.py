"""Unit tests for the booking_request Lambda handler."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from core.errors import ErrorCode, ValidationError


def _make_event(action: str | None = None, extra: dict | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "booking_id": "book-123",
        "employee_id": "emp-1",
        "user_query": "Fly from HYD to JFK next Monday",
    }
    if action:
        body["action"] = action
        body.setdefault("flight", {"id": "f-1"})
        body.setdefault("passengers", [{"name": "Alice"}])
        body.setdefault("search_url", "https://portal/search")
    if extra:
        body.update(extra)
    return {
        "requestContext": {"connectionId": "conn-abc"},
        "body": json.dumps(body),
    }


@patch("handlers.booking_request.get_sfn_client")
@patch("handlers.booking_request.get_dynamo_client")
@patch("handlers.booking_request.get_config")
def test_handler_starts_execution(mock_config, mock_dynamo, mock_sfn):
    from handlers.booking_request import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings", booking_workflow_arn="arn:aws:states:::sm")
    sfn = mock_sfn.return_value
    sfn.start_execution.return_value = {"executionArn": "arn:aws:states:::exec/1"}
    dynamo = mock_dynamo.return_value
    dynamo.query.return_value = {"Count": 0}

    result = handler(_make_event(), MagicMock())

    sfn.start_execution.assert_called_once()
    call_kwargs = sfn.start_execution.call_args[1]
    assert call_kwargs["stateMachineArn"] == "arn:aws:states:::sm"
    assert call_kwargs["name"] == "booking-book-123"
    payload = json.loads(call_kwargs["input"])
    assert payload["booking_id"] == "book-123"
    assert payload["employee_id"] == "emp-1"
    assert result["statusCode"] == 200
    assert json.loads(result["body"])["bookingId"] == "book-123"


@patch("handlers.booking_request.check_active_booking")
@patch("handlers.booking_request.get_sfn_client")
@patch("handlers.booking_request.get_dynamo_client")
@patch("handlers.booking_request.get_config")
def test_handler_rejects_active_booking(mock_config, mock_dynamo, mock_sfn, mock_guard):
    from handlers.booking_request import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings", booking_workflow_arn="arn:aws:states:::sm")
    mock_guard.side_effect = ValidationError("active", code=ErrorCode.VALIDATION_ERROR)

    result = handler(_make_event(), MagicMock())

    assert result["statusCode"] == 409
    mock_sfn.return_value.start_execution.assert_not_called()


@patch("handlers.booking_request.get_sfn_client")
@patch("handlers.booking_request.get_dynamo_client")
@patch("handlers.booking_request.get_config")
def test_handler_writes_booking_record(mock_config, mock_dynamo, mock_sfn):
    from handlers.booking_request import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings", booking_workflow_arn="arn:aws:states:::sm")
    sfn = mock_sfn.return_value
    sfn.start_execution.return_value = {"executionArn": "arn:aws:states:::exec/1"}
    dynamo = mock_dynamo.return_value
    dynamo.query.return_value = {"Count": 0}

    handler(_make_event(), MagicMock())

    dynamo.put_item.assert_called_once()
    item = dynamo.put_item.call_args[1]["Item"]
    assert item["status"]["S"] == "ACTIVE"
    assert item["employeeId"]["S"] == "emp-1"
    assert item["bookingId"]["S"] == "book-123"


@patch("handlers.booking_request.get_sfn_client")
@patch("handlers.booking_request.get_dynamo_client")
@patch("handlers.booking_request.get_config")
def test_handler_rejects_invalid_booking_id(mock_config, mock_dynamo, mock_sfn):
    from handlers.booking_request import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings", booking_workflow_arn="arn:aws:states:::sm")
    mock_dynamo.return_value.query.return_value = {"Count": 0}

    result = handler(_make_event(extra={"booking_id": "bad id!@#"}), MagicMock())

    assert result["statusCode"] == 409
    mock_sfn.return_value.start_execution.assert_not_called()


@patch("handlers.booking_request.get_sfn_client")
@patch("handlers.booking_request.get_dynamo_client")
@patch("handlers.booking_request.get_config")
def test_handler_rolls_back_on_sfn_failure(mock_config, mock_dynamo, mock_sfn):
    from handlers.booking_request import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings", booking_workflow_arn="arn:aws:states:::sm")
    dynamo = mock_dynamo.return_value
    dynamo.query.return_value = {"Count": 0}
    mock_sfn.return_value.start_execution.side_effect = RuntimeError("SFN unavailable")

    with pytest.raises(RuntimeError):
        handler(_make_event(), MagicMock())

    # update_item called to mark booking FAILED
    dynamo.update_item.assert_called()
    update_call = dynamo.update_item.call_args_list[0]
    assert update_call[1]["ExpressionAttributeValues"][":status"] == {"S": "FAILED"}


@patch("handlers.booking_request.pop_task_token")
@patch("handlers.booking_request.get_sfn_client")
@patch("handlers.booking_request.get_dynamo_client")
@patch("handlers.booking_request.get_config")
def test_handler_rejects_on_conditional_check_failure(mock_config, mock_dynamo, mock_sfn, mock_pop):
    """Race condition: guard passes but conditional put_item fails — should return 409."""
    from handlers.booking_request import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings", booking_workflow_arn="arn:aws:states:::sm")
    dynamo = mock_dynamo.return_value
    dynamo.query.return_value = {"Count": 0}
    dynamo.exceptions.ConditionalCheckFailedException = Exception
    dynamo.put_item.side_effect = Exception("ConditionalCheckFailedException")

    result = handler(_make_event(), MagicMock())

    assert result["statusCode"] == 409
    mock_sfn.return_value.start_execution.assert_not_called()


@patch("handlers.booking_request.get_sfn_client")
@patch("handlers.booking_request.get_dynamo_client")
@patch("handlers.booking_request.get_config")
def test_handler_persists_execution_arn(mock_config, mock_dynamo, mock_sfn):
    """After start_execution, executionArn is written back to the booking record."""
    from handlers.booking_request import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings", booking_workflow_arn="arn:aws:states:::sm")
    sfn = mock_sfn.return_value
    sfn.start_execution.return_value = {"executionArn": "arn:aws:states:::exec/1"}
    dynamo = mock_dynamo.return_value
    dynamo.query.return_value = {"Count": 0}

    handler(_make_event(), MagicMock())

    # update_item should be called to persist executionArn
    dynamo.update_item.assert_called_once()
    call = dynamo.update_item.call_args[1]
    assert call["ExpressionAttributeValues"][":arn"] == {"S": "arn:aws:states:::exec/1"}


@patch("handlers.booking_request.pop_task_token")
@patch("handlers.booking_request.get_sfn_client")
@patch("handlers.booking_request.get_dynamo_client")
@patch("handlers.booking_request.get_config")
def test_handler_select_flight_sends_task_success(mock_config, mock_dynamo, mock_sfn, mock_pop):
    from handlers.booking_request import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings", booking_workflow_arn="arn:aws:states:::sm")
    mock_pop.return_value = "token-xyz"

    result = handler(_make_event(action="select_flight"), MagicMock())

    mock_sfn.return_value.send_task_success.assert_called_once()
    call_kwargs = mock_sfn.return_value.send_task_success.call_args[1]
    assert call_kwargs["taskToken"] == "token-xyz"
    output = json.loads(call_kwargs["output"])
    assert "flight" in output
    assert result["statusCode"] == 200


@patch("handlers.booking_request.pop_task_token")
@patch("handlers.booking_request.get_sfn_client")
@patch("handlers.booking_request.get_dynamo_client")
@patch("handlers.booking_request.get_config")
def test_handler_select_flight_missing_token_raises(mock_config, mock_dynamo, mock_sfn, mock_pop):
    from handlers.booking_request import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings", booking_workflow_arn="arn:aws:states:::sm")
    mock_pop.side_effect = KeyError("No task token")

    with pytest.raises(KeyError):
        handler(_make_event(action="select_flight"), MagicMock())

    mock_sfn.return_value.send_task_success.assert_not_called()
