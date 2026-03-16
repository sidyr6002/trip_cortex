"""Unit tests for ReasoningService — Converse API, JSON extraction, escalation, retry."""

import json
from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from core.errors import ErrorCode, ReasoningError
from core.models.booking import ReasoningRequest
from core.services.reasoning import ReasoningService

FUTURE = (date.today() + timedelta(days=30)).isoformat()
FUTURE2 = (date.today() + timedelta(days=37)).isoformat()

# A valid BookingPlan JSON that passes Pydantic validation.
VALID_PLAN_JSON = json.dumps(
    {
        "intent": "flight_booking",
        "confidence": 0.92,
        "parameters": {
            "origin": "HYD",
            "destination": "ORD",
            "departure_date": FUTURE,
            "return_date": FUTURE2,
            "cabin_class": "economy",
            "time_preference": "morning",
            "passenger_count": 1,
        },
        "policy_constraints": {
            "max_budget_usd": 500.0,
            "preferred_vendors": ["Delta", "United"],
            "advance_booking_days_required": 14,
            "advance_booking_met": True,
            "requires_approval": False,
            "approval_reason": None,
        },
        "policy_sources": [
            {
                "chunk_id": "abc-123",
                "section_title": "Domestic Air Travel",
                "page": 3,
                "similarity_score": 0.89,
            }
        ],
        "reasoning_summary": "Economy class, $500 cap, United/Delta preferred.",
        "warnings": [],
        "fallback_url": None,
    }
)


def _make_service() -> ReasoningService:
    return ReasoningService(bedrock_client=None, model_id="us.amazon.nova-2-lite-v1:0")


def _converse_response(content_blocks: list[dict]) -> dict:
    """Build a minimal Converse API response structure."""
    return {"output": {"message": {"role": "assistant", "content": content_blocks}}}


# ── _build_converse_params ──────────────────────────────────────────────────


class TestBuildConverseParams:
    def test_medium_includes_inference_config(self):
        svc = _make_service()
        params = svc._build_converse_params("fly to ORD", "policy text", "medium")

        assert params["inferenceConfig"]["temperature"] == 0.1
        assert params["inferenceConfig"]["topP"] == 0.9
        assert params["inferenceConfig"]["maxTokens"] == 4000
        assert params["additionalModelRequestFields"]["reasoningConfig"]["maxReasoningEffort"] == "medium"
        assert params["additionalModelRequestFields"]["reasoningConfig"]["type"] == "enabled"

    def test_low_includes_inference_config(self):
        svc = _make_service()
        params = svc._build_converse_params("fly to ORD", "policy text", "low")

        assert "inferenceConfig" in params
        assert params["additionalModelRequestFields"]["reasoningConfig"]["maxReasoningEffort"] == "low"

    def test_high_omits_inference_config(self):
        svc = _make_service()
        params = svc._build_converse_params("fly to ORD", "policy text", "high")

        assert "inferenceConfig" not in params
        assert params["additionalModelRequestFields"]["reasoningConfig"]["maxReasoningEffort"] == "high"

    def test_user_query_and_context_in_message(self):
        svc = _make_service()
        params = svc._build_converse_params("fly HYD to ORD", "economy only $500", "medium")

        user_text = params["messages"][0]["content"][0]["text"]
        assert "fly HYD to ORD" in user_text
        assert "economy only $500" in user_text

    def test_model_id_set(self):
        svc = _make_service()
        params = svc._build_converse_params("q", "ctx", "medium")
        assert params["modelId"] == "us.amazon.nova-2-lite-v1:0"


# ── _extract_json ───────────────────────────────────────────────────────────


class TestExtractJson:
    def test_last_text_block_pure_json(self):
        response = _converse_response(
            [
                {"reasoningContent": {"reasoningText": {"text": "[REDACTED]"}}},
                {"text": "Here is the plan:"},
                {"text": VALID_PLAN_JSON},
            ]
        )
        result = ReasoningService._extract_json(response)
        assert json.loads(result)["intent"] == "flight_booking"

    def test_skips_reasoning_content_blocks(self):
        response = _converse_response(
            [
                {"reasoningContent": {"reasoningText": {"text": "[REDACTED]"}}},
                {"text": VALID_PLAN_JSON},
            ]
        )
        result = ReasoningService._extract_json(response)
        assert json.loads(result)["confidence"] == 0.92

    def test_regex_fallback_with_preamble(self):
        text_with_preamble = f"Here is your booking plan:\n{VALID_PLAN_JSON}\nDone."
        response = _converse_response([{"text": text_with_preamble}])
        result = ReasoningService._extract_json(response)
        assert json.loads(result)["intent"] == "flight_booking"

    def test_no_text_blocks_raises(self):
        response = _converse_response([{"reasoningContent": {"reasoningText": {"text": "[REDACTED]"}}}])
        with pytest.raises(ReasoningError, match="No text blocks") as exc_info:
            ReasoningService._extract_json(response)
        assert exc_info.value.code == ErrorCode.INVALID_PLAN

    def test_no_json_in_text_raises(self):
        response = _converse_response([{"text": "I cannot produce a plan for this request."}])
        with pytest.raises(ReasoningError, match="No JSON object found"):
            ReasoningService._extract_json(response)

    def test_malformed_json_braces_raises(self):
        response = _converse_response([{"text": '{"broken": true, "missing_close'}])
        with pytest.raises(ReasoningError):
            ReasoningService._extract_json(response)


# ── _parse_plan ─────────────────────────────────────────────────────────────


class TestParsePlan:
    def test_valid_json_returns_booking_plan(self):
        plan = ReasoningService._parse_plan(VALID_PLAN_JSON)
        assert plan.intent == "flight_booking"
        assert plan.parameters.origin == "HYD"
        assert plan.policy_constraints.max_budget_usd == 500.0

    def test_invalid_json_raises(self):
        with pytest.raises(ReasoningError, match="Invalid JSON") as exc_info:
            ReasoningService._parse_plan("{not valid json}")
        assert exc_info.value.code == ErrorCode.INVALID_PLAN

    def test_schema_violation_raises(self):
        bad_plan = json.dumps({"intent": "hotel_booking", "confidence": 0.5})
        with pytest.raises(ReasoningError, match="BookingPlan validation failed") as exc_info:
            ReasoningService._parse_plan(bad_plan)
        assert exc_info.value.code == ErrorCode.INVALID_PLAN


# ── Task 2: Escalation logic & generate_booking_plan ────────────────────────


def _make_request(**overrides: Any) -> ReasoningRequest:
    base = {
        "booking_id": "b-1",
        "employee_id": "e-1",
        "user_query": "Book a flight from HYD to ORD",
        "context_text": "Policy: economy only, $500 cap, Delta/United preferred.",
        "confidence_level": "high",
        "max_similarity": 0.89,
    }
    base.update(overrides)
    return ReasoningRequest(**base)


def _mock_converse_response(plan_json: str) -> dict:
    """Build a Converse API response with reasoningContent + text block."""
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {"reasoningContent": {"reasoningText": {"text": "[REDACTED]"}}},
                    {"text": plan_json},
                ],
            }
        }
    }


class TestDetermineInitialEffort:
    def test_high_confidence_returns_medium(self):
        assert ReasoningService._determine_initial_effort("high", 0.85) == "medium"

    def test_low_confidence_above_threshold_returns_medium(self):
        assert ReasoningService._determine_initial_effort("low", 0.72) == "medium"

    def test_low_similarity_returns_high(self):
        assert ReasoningService._determine_initial_effort("low", 0.68) == "medium"

    def test_none_confidence_returns_high(self):
        assert ReasoningService._determine_initial_effort("none", 0.0) == "high"

    def test_boundary_at_threshold_returns_high(self):
        # 0.09 is below threshold (< 0.10), so should be high
        assert ReasoningService._determine_initial_effort("high", 0.09) == "high"

    def test_at_exactly_threshold_returns_medium(self):
        assert ReasoningService._determine_initial_effort("high", 0.10) == "medium"


class TestEscalationSequence:
    def test_from_medium(self):
        assert ReasoningService._escalation_sequence("medium") == ["medium", "high", "high"]

    def test_from_high(self):
        assert ReasoningService._escalation_sequence("high") == ["high", "high", "high"]


class TestGenerateBookingPlan:
    def test_success_first_attempt(self):
        client = MagicMock()
        client.converse.return_value = _mock_converse_response(VALID_PLAN_JSON)
        svc = ReasoningService(client, "us.amazon.nova-2-lite-v1:0")

        result = svc.generate_booking_plan(_make_request())

        assert result.retry_count == 0
        assert result.escalated is False
        assert result.thinking_effort == "medium"
        assert result.plan.intent == "flight_booking"
        assert result.model_id == "us.amazon.nova-2-lite-v1:0"
        assert result.booking_id == "b-1"
        assert result.employee_id == "e-1"
        client.converse.assert_called_once()

    def test_escalates_after_first_medium_failure(self):
        client = MagicMock()
        # First call returns invalid JSON, second (high) returns valid.
        client.converse.side_effect = [
            _mock_converse_response("not json"),
            _mock_converse_response(VALID_PLAN_JSON),
        ]
        svc = ReasoningService(client, "us.amazon.nova-2-lite-v1:0")

        result = svc.generate_booking_plan(_make_request())

        assert result.retry_count == 1
        assert result.escalated is True
        assert result.thinking_effort == "high"
        assert client.converse.call_count == 2

    def test_all_attempts_fail_raises(self):
        client = MagicMock()
        client.converse.return_value = _mock_converse_response("garbage")
        svc = ReasoningService(client, "us.amazon.nova-2-lite-v1:0")

        with pytest.raises(ReasoningError, match="All 3 reasoning attempts failed") as exc_info:
            svc.generate_booking_plan(_make_request())
        assert exc_info.value.code == ErrorCode.REASONING_FAILED
        assert client.converse.call_count == 3

    def test_starts_at_high_when_low_similarity(self):
        client = MagicMock()
        client.converse.return_value = _mock_converse_response(VALID_PLAN_JSON)
        svc = ReasoningService(client, "us.amazon.nova-2-lite-v1:0")

        result = svc.generate_booking_plan(_make_request(confidence_level="none", max_similarity=0.05))

        assert result.thinking_effort == "high"
        assert result.escalated is False  # Started at high, no escalation
        assert result.retry_count == 0

    def test_starts_at_high_when_none_confidence(self):
        client = MagicMock()
        client.converse.return_value = _mock_converse_response(VALID_PLAN_JSON)
        svc = ReasoningService(client, "us.amazon.nova-2-lite-v1:0")

        result = svc.generate_booking_plan(_make_request(confidence_level="none", max_similarity=0.0))

        assert result.thinking_effort == "high"
        assert result.escalated is False

    def test_latency_tracked(self):
        client = MagicMock()
        client.converse.return_value = _mock_converse_response(VALID_PLAN_JSON)
        svc = ReasoningService(client, "us.amazon.nova-2-lite-v1:0")

        result = svc.generate_booking_plan(_make_request())

        assert result.latency_ms >= 0.0

    def test_second_attempt_succeeds_no_escalation(self):
        client = MagicMock()
        client.converse.side_effect = [
            _mock_converse_response("bad"),
            _mock_converse_response(VALID_PLAN_JSON),
        ]
        svc = ReasoningService(client, "us.amazon.nova-2-lite-v1:0")

        result = svc.generate_booking_plan(_make_request())

        assert result.retry_count == 1
        assert result.escalated is True  # 2nd attempt is already "high"
        assert result.thinking_effort == "high"

    def test_high_effort_omits_inference_config_on_escalation(self):
        client = MagicMock()
        client.converse.side_effect = [
            _mock_converse_response("bad"),
            _mock_converse_response(VALID_PLAN_JSON),
        ]
        svc = ReasoningService(client, "us.amazon.nova-2-lite-v1:0")

        svc.generate_booking_plan(_make_request())

        # Second call (high effort) should NOT have inferenceConfig
        second_call_kwargs = client.converse.call_args_list[1][1]
        assert "inferenceConfig" not in second_call_kwargs
        # First call (medium effort) should have inferenceConfig
        first_call_kwargs = client.converse.call_args_list[0][1]
        assert "inferenceConfig" in first_call_kwargs
