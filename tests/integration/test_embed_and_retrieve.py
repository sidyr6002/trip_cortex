"""Integration test: full embed_and_retrieve handler chain against local Aurora + DynamoDB."""

from unittest.mock import patch

import pytest
from psycopg.types.json import Json


def _make_vector(value: float) -> list[float]:
    return [value] * 1024


def _vec_str(value: float) -> str:
    return "[" + ",".join([str(value)] * 1024) + "]"


@pytest.fixture
def seeded_chunks(pg_connection, pg_policy_id):
    """Insert 3 policy chunks with known embeddings; clean up on teardown."""
    rows = [
        (
            pg_policy_id,
            "text",
            "Economy class only for domestic flights.",
            3,
            "Domestic Air Travel",
            "bda-e-001",
            _vec_str(0.9),
        ),
        (
            pg_policy_id,
            "table",
            "Max budget: $500 domestic, $1500 international.",
            7,
            "Expense Limits",
            "bda-e-002",
            _vec_str(0.5),
        ),
        (pg_policy_id, "text", "Book at least 14 days in advance.", 5, "Booking Deadlines", "bda-e-003", _vec_str(0.1)),
    ]
    with pg_connection.cursor() as cur:
        for policy_id, ctype, text, page, section, entity_id, vec in rows:
            cur.execute(
                """
                INSERT INTO policy_chunks
                    (policy_id, content_type, content_text, source_page, section_title,
                     bda_entity_id, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s)
                """,
                (policy_id, ctype, text, page, section, entity_id, vec, Json({})),
            )
        pg_connection.commit()
    yield
    # pg_policy_id fixture handles cascade delete of chunks


@pytest.mark.integration
def test_handler_returns_valid_response(seeded_chunks):
    """Full chain: handler → PolicyRetrievalService → Aurora → DynamoDB audit."""
    # Query vector close to chunk 1 (0.9 * 1024) → high similarity
    query_embedding = _make_vector(0.89)

    with patch("core.services.query_embedding.QueryEmbeddingService.embed_query", return_value=query_embedding):
        from handlers.embed_and_retrieve import handler

        response = handler(
            {"booking_id": "b-integ-1", "employee_id": "emp-integ-1", "user_query": "book a domestic flight"},
            None,
        )

    assert response["booking_id"] == "b-integ-1"
    assert response["employee_id"] == "emp-integ-1"
    assert response["total_chunks"] >= 1
    assert response["retrieval_latency_ms"] > 0
    assert response["context_text"] != ""


@pytest.mark.integration
def test_handler_confidence_level_is_high_for_close_vector(seeded_chunks):
    """Vector close to 0.9-chunk yields HIGH confidence."""
    query_embedding = _make_vector(0.89)

    with patch("core.services.query_embedding.QueryEmbeddingService.embed_query", return_value=query_embedding):
        from handlers.embed_and_retrieve import handler

        response = handler(
            {"booking_id": "b-integ-2", "employee_id": "emp-integ-2", "user_query": "domestic flight policy"},
            None,
        )

    assert response["confidence"]["level"] == "high"
    assert response["confidence"]["max_similarity"] > 0.75


@pytest.mark.integration
def test_handler_writes_audit_record(seeded_chunks, audit_log_table):
    """Audit record is written to DynamoDB with correct bookingId."""
    import boto3

    from core.config import get_config

    config = get_config()
    dynamo_client = boto3.client(
        "dynamodb",
        endpoint_url=config.dynamodb_endpoint,
        region_name=config.aws_region,
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    )
    query_embedding = _make_vector(0.89)

    with (
        patch("core.services.query_embedding.QueryEmbeddingService.embed_query", return_value=query_embedding),
        patch("handlers.embed_and_retrieve.get_dynamo_client", return_value=dynamo_client),
        patch("handlers.embed_and_retrieve.get_config") as mock_cfg,
    ):
        mock_cfg.return_value = config.__class__(**{**config.model_dump(), "audit_log_table": "TripCortexAuditLog"})
        from handlers.embed_and_retrieve import handler

        handler(
            {"booking_id": "b-integ-audit", "employee_id": "emp-integ-3", "user_query": "flight booking policy"},
            None,
        )

    items = audit_log_table.scan(
        FilterExpression="bookingId = :bid",
        ExpressionAttributeValues={":bid": "b-integ-audit"},
    )["Items"]
    assert len(items) == 1
    assert items[0]["event"] == "policy_retrieval"
    assert items[0]["employeeId"] == "emp-integ-3"
    assert "user_query" not in items[0]
    assert "query_text" not in items[0]


@pytest.mark.integration
def test_handler_no_chunks_returns_none_confidence(pg_connection, pg_policy_id):
    """When query vector is far from all stored chunks, confidence is none."""
    # Insert one chunk with a very specific vector
    with pg_connection.cursor() as cur:
        cur.execute(
            "INSERT INTO policy_chunks (policy_id, content_type, content_text, embedding, bda_entity_id) "
            "VALUES (%s, 'text', 'some policy', %s::vector, 'bda-far-001')",
            (pg_policy_id, _vec_str(0.9)),
        )
        pg_connection.commit()

    # Query with orthogonal vector — similarity will be below 0.65 threshold
    query_embedding = _make_vector(0.0)
    query_embedding[0] = 1.0  # unit vector in dim-0 only, orthogonal to [0.9]*1024

    with patch("core.services.query_embedding.QueryEmbeddingService.embed_query", return_value=query_embedding):
        from handlers.embed_and_retrieve import handler

        response = handler(
            {"booking_id": "b-integ-none", "employee_id": "emp-integ-4", "user_query": "unrelated query"},
            None,
        )

    assert response["confidence"]["level"] in ("none", "low")
