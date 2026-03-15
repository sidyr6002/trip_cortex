"""Reasoning service — invokes Nova 2 Lite via Bedrock Converse API with Extended Thinking."""

import json
import time
from typing import Any

import structlog
from pydantic import ValidationError as PydanticValidationError

from core.errors import ErrorCode, ReasoningError
from core.models.booking import BookingPlan, ReasoningRequest, ReasoningResult, ThinkingEffort

logger = structlog.get_logger()

# ── Prompt constants ────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a corporate travel policy compliance engine.\n"
    "Given an employee's travel request and the relevant policy excerpts, "
    "produce a structured JSON booking plan.\n\n"
    "Rules:\n"
    "- Always enforce the strictest applicable policy constraint.\n"
    "- If a parameter cannot be determined from the request or policy, set it to null.\n"
    "- Use IATA 3-letter airport codes (uppercase) for origin and destination.\n"
    "- Dates must be ISO 8601 format (YYYY-MM-DD).\n"
    "- cabin_class must be one of: economy, premium_economy, business, first.\n"
    "- Respond with ONLY the JSON object. No markdown fences, no explanation, no preamble."
)

USER_PROMPT_TEMPLATE = (
    "EMPLOYEE REQUEST:\n{user_request}\n\n"
    "RELEVANT POLICY EXCERPTS:\n{policy_context}\n\n"
    "Produce a JSON booking plan with this exact schema:\n"
    "{{\n"
    '  "intent": "flight_booking | flight_search | policy_query",\n'
    '  "confidence": 0.0-1.0,\n'
    '  "parameters": {{\n'
    '    "origin": "IATA code",\n'
    '    "destination": "IATA code",\n'
    '    "departure_date": "YYYY-MM-DD",\n'
    '    "return_date": "YYYY-MM-DD or null",\n'
    '    "cabin_class": "economy|premium_economy|business|first",\n'
    '    "time_preference": "morning|afternoon|evening|red_eye or null",\n'
    '    "passenger_count": 1\n'
    "  }},\n"
    '  "policy_constraints": {{\n'
    '    "max_budget_usd": number,\n'
    '    "preferred_vendors": ["airline names"],\n'
    '    "advance_booking_days_required": number or null,\n'
    '    "advance_booking_met": true|false,\n'
    '    "requires_approval": true|false,\n'
    '    "approval_reason": "string or null"\n'
    "  }},\n"
    '  "policy_sources": [{{\n'
    '    "chunk_id": "id from the policy excerpt",\n'
    '    "section_title": "section name",\n'
    '    "page": page_number,\n'
    '    "similarity_score": 0.0-1.0\n'
    "  }}],\n"
    '  "reasoning_summary": "Brief explanation of how policy was applied",\n'
    '  "warnings": [],\n'
    '  "fallback_url": null\n'
    "}}"
)


# ── Service ─────────────────────────────────────────────────────────────────


class ReasoningService:
    """Invokes Nova 2 Lite Converse API and validates output against BookingPlan."""

    def __init__(self, bedrock_client: Any, model_id: str) -> None:
        self._client = bedrock_client
        self._model_id = model_id

    def _build_converse_params(self, user_query: str, context_text: str, effort: ThinkingEffort) -> dict[str, Any]:
        """Build kwargs for bedrock_client.converse()."""
        params: dict[str, Any] = {
            "modelId": self._model_id,
            "system": [{"text": SYSTEM_PROMPT}],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": USER_PROMPT_TEMPLATE.format(
                                user_request=user_query,
                                policy_context=context_text,
                            )
                        }
                    ],
                }
            ],
            "additionalModelRequestFields": {
                "reasoningConfig": {
                    "type": "enabled",
                    "maxReasoningEffort": effort,
                }
            },
        }
        # When high effort, model controls output autonomously — do NOT set inferenceConfig.
        if effort != "high":
            params["inferenceConfig"] = {
                "temperature": 0.1,
                "topP": 0.9,
                "maxTokens": 4000,
            }
        return params

    @staticmethod
    def _extract_json(response: dict[str, Any]) -> str:
        """Extract JSON string from the last text block in the Converse response.

        Skips reasoningContent blocks. Falls back to brace-depth extraction
        if the last text block contains preamble text around the JSON.

        Raises:
            ReasoningError: If no JSON object can be extracted.
        """
        text_blocks: list[str] = [
            block["text"] for block in response["output"]["message"]["content"] if "text" in block
        ]

        if not text_blocks:
            raise ReasoningError(
                "No text blocks in Converse response",
                code=ErrorCode.INVALID_PLAN,
            )

        raw = text_blocks[-1].strip()

        # Fast path: entire block is valid JSON.
        if raw.startswith("{"):
            try:
                json.loads(raw)
                return raw
            except json.JSONDecodeError:
                pass

        # Fallback: extract first top-level {...} using brace-depth counter.
        start = raw.find("{")
        if start == -1:
            raise ReasoningError(
                "No JSON object found in model response",
                code=ErrorCode.INVALID_PLAN,
            )

        depth = 0
        for i in range(start, len(raw)):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = raw[start : i + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except json.JSONDecodeError:
                        break

        raise ReasoningError(
            "Failed to extract valid JSON from model response",
            code=ErrorCode.INVALID_PLAN,
        )

    @staticmethod
    def _parse_plan(raw_json: str) -> BookingPlan:
        """Parse raw JSON string into a validated BookingPlan.

        Raises:
            ReasoningError: On JSON decode failure or Pydantic validation failure.
        """
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise ReasoningError(
                f"Invalid JSON from model: {e}",
                code=ErrorCode.INVALID_PLAN,
            ) from e

        try:
            return BookingPlan.model_validate(data)
        except PydanticValidationError as e:
            raise ReasoningError(
                f"BookingPlan validation failed: {e.error_count()} errors — {e.errors()[0]['msg']}",
                code=ErrorCode.INVALID_PLAN,
            ) from e

    # ── Escalation logic ────────────────────────────────────────────────────

    _LOW_SIMILARITY_THRESHOLD = 0.70

    @staticmethod
    def _determine_initial_effort(confidence_level: str, max_similarity: float) -> ThinkingEffort:
        """Pick starting effort based on retrieval confidence.

        Returns "high" when confidence is "none" or similarity is below threshold,
        "medium" otherwise.
        """
        if confidence_level == "none" or max_similarity < ReasoningService._LOW_SIMILARITY_THRESHOLD:
            return "high"
        return "medium"

    @staticmethod
    def _escalation_sequence(initial: ThinkingEffort) -> list[ThinkingEffort]:
        """Return the 3-attempt escalation ladder.

        medium start → [medium, medium, high]
        high start   → [high, high, high]
        """
        if initial == "high":
            return ["high", "high", "high"]
        return ["medium", "medium", "high"]

    def generate_booking_plan(self, request: ReasoningRequest, remaining_ms: int = 300_000) -> ReasoningResult:
        """Invoke Nova 2 Lite with in-service retry and dynamic escalation.

        Escalation ladder: attempt 1 (initial) → attempt 2 (initial) → attempt 3 (high).
        If all 3 attempts fail, raises ReasoningError for Step Functions graceful degradation.

        Args:
            remaining_ms: Milliseconds remaining in the Lambda invocation
                          (from context.get_remaining_time_in_millis()). Used to skip
                          attempts when insufficient time remains to avoid a hard Lambda timeout.
        """
        _MIN_ATTEMPT_MS = 30_000  # don't start an attempt with less than 30s left

        initial_effort = self._determine_initial_effort(request.confidence_level, request.max_similarity)
        sequence = self._escalation_sequence(initial_effort)
        errors: list[str] = []
        start = time.monotonic()

        for attempt, effort in enumerate(sequence):
            elapsed_ms = (time.monotonic() - start) * 1000
            if remaining_ms - elapsed_ms < _MIN_ATTEMPT_MS:
                errors.append(f"attempt {attempt + 1} ({effort}): skipped — insufficient time remaining")
                logger.warning("reasoning_attempt_skipped", attempt=attempt + 1, effort=effort)
                break

            try:
                params = self._build_converse_params(request.user_query, request.context_text, effort)
                response = self._client.converse(**params)
                raw_json = self._extract_json(response)
                plan = self._parse_plan(raw_json)

                return ReasoningResult(
                    booking_id=request.booking_id,
                    employee_id=request.employee_id,
                    plan=plan,
                    model_id=self._model_id,
                    thinking_effort=effort,
                    latency_ms=round((time.monotonic() - start) * 1000, 1),
                    retry_count=attempt,
                    escalated=effort != initial_effort,
                )
            except ReasoningError as e:
                errors.append(f"attempt {attempt + 1} ({effort}): {e.message}")
                logger.warning(
                    "reasoning_attempt_failed",
                    attempt=attempt + 1,
                    effort=effort,
                    error_code=e.code.value,
                )

        raise ReasoningError(
            f"All {len(sequence)} reasoning attempts failed: {'; '.join(errors)}",
            code=ErrorCode.REASONING_FAILED,
        )
