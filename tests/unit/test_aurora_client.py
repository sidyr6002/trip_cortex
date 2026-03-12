"""Unit tests for AuroraClient."""

from unittest.mock import MagicMock, call, patch

import pytest

from core.db.aurora import AuroraClient
from core.errors import PolicyRetrievalError


@pytest.fixture
def client():
    cfg = MagicMock()
    cfg.aurora_secret_arn = None
    cfg.aurora_host = "localhost"
    cfg.aurora_port = 5432
    cfg.aurora_database = "tripcortex"
    cfg.aurora_user = "tripcortex"
    cfg.aurora_password = "localdev"
    c = AuroraClient(cfg)
    # Inject a mock connection
    mock_conn = MagicMock()
    mock_conn.closed = False
    c._conn = mock_conn
    return c, mock_conn


def test_similarity_search_sets_ef_search_before_query(client):
    """SET LOCAL hnsw.ef_search must be issued before the similarity query."""
    aurora, mock_conn = client

    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_conn.transaction.return_value.__enter__ = MagicMock(return_value=None)
    mock_conn.transaction.return_value.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    aurora.similarity_search([0.1] * 1024, ef_search=100)

    execute_calls = mock_cur.execute.call_args_list
    assert execute_calls[0] == call(f"SET LOCAL hnsw.ef_search = {100}")
    assert execute_calls[1][0][0].strip().startswith("WITH query AS")


def test_similarity_search_default_ef_search(client):
    """Default ef_search of 40 is used when not specified."""
    aurora, mock_conn = client

    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_conn.transaction.return_value.__enter__ = MagicMock(return_value=None)
    mock_conn.transaction.return_value.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    aurora.similarity_search([0.1] * 1024)

    first_call = mock_cur.execute.call_args_list[0]
    assert first_call == call(f"SET LOCAL hnsw.ef_search = {40}")


def test_verify_hnsw_index_true(client):
    """verify_hnsw_index() returns True when index exists with correct config."""
    aurora, mock_conn = client

    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = (
        "CREATE INDEX idx_policy_chunks_embedding ON policy_chunks USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64')",
    )
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    assert aurora.verify_hnsw_index() is True


def test_verify_hnsw_index_missing(client):
    """verify_hnsw_index() returns False when index does not exist."""
    aurora, mock_conn = client

    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = None
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    assert aurora.verify_hnsw_index() is False
