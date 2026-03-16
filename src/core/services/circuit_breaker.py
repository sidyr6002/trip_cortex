"""DynamoDB-backed circuit breaker for travel portal availability."""

import time
from typing import Any

import structlog

from core.models.circuit_breaker import CircuitBreakerState, CircuitState

log = structlog.get_logger()


class CircuitBreakerService:
    def __init__(
        self,
        dynamo_client: Any,
        table_name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
    ) -> None:
        self._client = dynamo_client
        self._table = table_name
        self._threshold = failure_threshold
        self._recovery_timeout = recovery_timeout

    def get_state(self, circuit_id: str) -> CircuitBreakerState:
        resp = self._client.get_item(
            TableName=self._table,
            Key={"circuitId": {"S": circuit_id}},
        )
        item = resp.get("Item")
        if not item:
            return CircuitBreakerState(
                circuit_id=circuit_id, recovery_timeout=self._recovery_timeout
            )
        return CircuitBreakerState(
            circuit_id=circuit_id,
            state=CircuitState(item.get("state", {}).get("S", CircuitState.CLOSED.value)),
            failure_count=int(item["failureCount"]["N"]),
            last_failure_time=float(item["lastFailureTime"]["N"]),
            recovery_timeout=int(item.get("recoveryTimeout", {}).get("N", self._recovery_timeout)),
            ttl=int(item.get("ttl", {}).get("N", 0)),
        )

    def can_execute(self, circuit_id: str) -> bool:
        state = self.get_state(circuit_id)

        if state.state == CircuitState.CLOSED:
            return True

        if state.state == CircuitState.HALF_OPEN:
            return True

        # OPEN — check if recovery timeout has elapsed
        if time.time() - state.last_failure_time <= state.recovery_timeout:
            return False

        # Attempt atomic OPEN → HALF_OPEN transition
        try:
            self._client.update_item(
                TableName=self._table,
                Key={"circuitId": {"S": circuit_id}},
                UpdateExpression="SET #s = :half_open",
                ConditionExpression="#s = :open",
                ExpressionAttributeNames={"#s": "state"},
                ExpressionAttributeValues={
                    ":half_open": {"S": CircuitState.HALF_OPEN.value},
                    ":open": {"S": CircuitState.OPEN.value},
                },
            )
            log.info("circuit_state_changed", circuit_id=circuit_id, from_state="open", to_state="half_open")
            return True
        except self._client.exceptions.ConditionalCheckFailedException:
            # Another Lambda already transitioned — treat as still OPEN
            return False

    def record_failure(self, circuit_id: str) -> CircuitBreakerState:
        now = time.time()
        ttl = int(now) + 86400

        # Atomically increment failure count
        resp = self._client.update_item(
            TableName=self._table,
            Key={"circuitId": {"S": circuit_id}},
            UpdateExpression="ADD failureCount :one SET lastFailureTime = :now, recoveryTimeout = :rt, #ttl = :ttl",
            ExpressionAttributeNames={"#ttl": "ttl"},
            ExpressionAttributeValues={
                ":one": {"N": "1"},
                ":now": {"N": str(now)},
                ":rt": {"N": str(self._recovery_timeout)},
                ":ttl": {"N": str(ttl)},
            },
            ReturnValues="ALL_NEW",
        )
        new_count = int(resp["Attributes"]["failureCount"]["N"])

        # Conditionally flip to OPEN if threshold reached and not already OPEN
        if new_count >= self._threshold:
            try:
                self._client.update_item(
                    TableName=self._table,
                    Key={"circuitId": {"S": circuit_id}},
                    UpdateExpression="SET #s = :open",
                    ConditionExpression="#s <> :open",
                    ExpressionAttributeNames={"#s": "state"},
                    ExpressionAttributeValues={
                        ":open": {"S": CircuitState.OPEN.value},
                    },
                )
                log.warning(
                    "circuit_state_changed",
                    circuit_id=circuit_id,
                    from_state="closed",
                    to_state="open",
                    failure_count=new_count,
                )
            except self._client.exceptions.ConditionalCheckFailedException:
                pass  # Already OPEN — idempotent

        return self.get_state(circuit_id)

    def record_success(self, circuit_id: str) -> CircuitBreakerState:
        self._client.update_item(
            TableName=self._table,
            Key={"circuitId": {"S": circuit_id}},
            UpdateExpression="SET #s = :closed, failureCount = :zero, #ttl = :ttl",
            ExpressionAttributeNames={"#s": "state", "#ttl": "ttl"},
            ExpressionAttributeValues={
                ":closed": {"S": CircuitState.CLOSED.value},
                ":zero": {"N": "0"},
                ":ttl": {"N": str(int(time.time()) + 86400)},
            },
        )
        log.info("circuit_state_changed", circuit_id=circuit_id, to_state="closed")
        return self.get_state(circuit_id)
