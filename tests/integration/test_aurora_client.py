"""Integration tests for AuroraClient and new schema constraints."""

import psycopg.errors
import pytest

from core.config import get_config
from core.db import AuroraClient

# ── Helpers ───────────────────────────────────────────────────────────────────


def _vec_str(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


# ── Schema constraint tests ───────────────────────────────────────────────────


@pytest.mark.integration
def test_policies_table_exists(pg_connection):
    with pg_connection.cursor() as cur:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'policies' ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cur.fetchall()]
    assert "id" in columns
    assert "source_s3_uri" in columns
    assert "status" in columns
    assert "version" in columns


@pytest.mark.integration
def test_policy_chunks_fk_constraint(pg_connection):
    import uuid

    vec = _vec_str([0.1] * 1024)
    with pg_connection.cursor() as cur:
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            cur.execute(
                """
                INSERT INTO policy_chunks (policy_id, content_type, embedding)
                VALUES (%s, 'text', %s::vector)
            """,
                (uuid.uuid4(), vec),
            )
    pg_connection.rollback()


@pytest.mark.integration
def test_cascade_delete(pg_connection, pg_policy_id):
    vec = _vec_str([0.1] * 1024)
    with pg_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO policy_chunks (policy_id, content_type, embedding)
            VALUES (%s, 'text', %s::vector)
        """,
            (pg_policy_id, vec),
        )
        pg_connection.commit()

        cur.execute("DELETE FROM policies WHERE id = %s", (pg_policy_id,))
        pg_connection.commit()

        cur.execute("SELECT COUNT(*) FROM policy_chunks WHERE policy_id = %s", (pg_policy_id,))
        assert cur.fetchone()[0] == 0


@pytest.mark.integration
def test_content_type_check_constraint(pg_connection, pg_policy_id):
    vec = _vec_str([0.1] * 1024)
    with pg_connection.cursor() as cur:
        with pytest.raises(psycopg.errors.CheckViolation):
            cur.execute(
                """
                INSERT INTO policy_chunks (policy_id, content_type, embedding)
                VALUES (%s, 'invalid', %s::vector)
            """,
                (pg_policy_id, vec),
            )
    pg_connection.rollback()


# ── AuroraClient tests ────────────────────────────────────────────────────────


@pytest.mark.integration
def test_aurora_client_health_check():
    with AuroraClient(get_config()) as client:
        assert client.health_check() is True


@pytest.mark.integration
def test_aurora_client_similarity_search(pg_connection, pg_policy_id):
    # Insert two chunks: one similar to query, one dissimilar
    similar_vec = [1.0] * 512 + [0.0] * 512
    dissimilar_vec = [0.0] * 512 + [1.0] * 512

    with pg_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO policy_chunks (policy_id, content_type, content_text, embedding)
            VALUES
                (%s, 'text', 'relevant policy text', %s::vector),
                (%s, 'text', 'unrelated content', %s::vector)
        """,
            (pg_policy_id, _vec_str(similar_vec), pg_policy_id, _vec_str(dissimilar_vec)),
        )
        pg_connection.commit()

    with AuroraClient(get_config()) as client:
        results = client.similarity_search(similar_vec, threshold=0.5, top_k=5)

    assert len(results) >= 1
    assert results[0].content_text == "relevant policy text"
    assert results[0].similarity >= 0.5
    # Results ordered by descending similarity
    similarities = [r.similarity for r in results]
    assert similarities == sorted(similarities, reverse=True)


@pytest.mark.integration
def test_aurora_client_similarity_search_empty(pg_connection, pg_policy_id):
    vec = [1.0] * 512 + [0.0] * 512
    with pg_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO policy_chunks (policy_id, content_type, embedding)
            VALUES (%s, 'text', %s::vector)
        """,
            (pg_policy_id, _vec_str(vec)),
        )
        pg_connection.commit()

    # Threshold of 1.0 excludes everything except perfect matches
    query = [0.0] * 512 + [1.0] * 512
    with AuroraClient(get_config()) as client:
        results = client.similarity_search(query, threshold=1.0, top_k=5)

    assert results == []
