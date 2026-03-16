"""Unit tests for task_token service."""

from time import time
from unittest.mock import MagicMock

import pytest

from core.services.task_token import pop_task_token, store_task_token


def test_store_task_token_writes_with_ttl():
    dynamo = MagicMock()
    before = int(time()) + 7200

    store_task_token(dynamo, "Bookings", "book-1", "emp-1", "tok-abc")

    after = int(time()) + 7200
    dynamo.update_item.assert_called_once()
    call = dynamo.update_item.call_args[1]
    assert call["Key"] == {"employeeId": {"S": "emp-1"}, "bookingId": {"S": "book-1"}}
    assert call["ExpressionAttributeValues"][":t"] == {"S": "tok-abc"}
    ttl = int(call["ExpressionAttributeValues"][":e"]["N"])
    assert before <= ttl <= after


def test_pop_task_token_returns_and_clears():
    dynamo = MagicMock()
    dynamo.get_item.return_value = {"Item": {"taskToken": {"S": "tok-xyz"}}}

    token = pop_task_token(dynamo, "Bookings", "book-1", "emp-1")

    assert token == "tok-xyz"
    dynamo.update_item.assert_called_once()
    call = dynamo.update_item.call_args[1]
    assert "REMOVE taskToken" in call["UpdateExpression"]


def test_pop_task_token_missing_raises_key_error():
    dynamo = MagicMock()
    dynamo.get_item.return_value = {"Item": {}}  # item exists but no taskToken

    with pytest.raises(KeyError):
        pop_task_token(dynamo, "Bookings", "book-1", "emp-1")


def test_pop_task_token_no_item_raises_key_error():
    dynamo = MagicMock()
    dynamo.get_item.return_value = {}  # no Item key at all

    with pytest.raises(KeyError):
        pop_task_token(dynamo, "Bookings", "book-1", "emp-1")
