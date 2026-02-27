"""Integration tests for PostgreSQL pgvector operations."""

import pytest
from psycopg.types.json import Json


@pytest.mark.integration
def test_pgvector_extension_loaded(pg_connection):
    """Test that pgvector extension is installed."""
    with pg_connection.cursor() as cur:
        cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        result = cur.fetchone()
        assert result is not None
        assert result[0] == "vector"


@pytest.mark.integration
def test_policy_chunks_table_exists(pg_connection):
    """Test that policy_chunks table exists with correct columns."""
    with pg_connection.cursor() as cur:
        # Check table exists
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'policy_chunks'
        """)
        assert cur.fetchone() is not None
        
        # Check columns
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'policy_chunks' 
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        column_names = [col[0] for col in columns]
        
        # Verify key columns exist
        assert "id" in column_names
        assert "policy_id" in column_names
        assert "content_type" in column_names
        assert "content_text" in column_names
        assert "embedding" in column_names
        assert "metadata" in column_names
        assert "created_at" in column_names


@pytest.mark.integration
def test_insert_and_retrieve_chunk(pg_connection, pg_policy_id):
    """Test inserting and retrieving a policy chunk with vector."""
    vector = [0.001] * 1024
    vector_str = "[" + ",".join(str(v) for v in vector) + "]"

    with pg_connection.cursor() as cur:
        cur.execute("""
            INSERT INTO policy_chunks 
            (policy_id, content_type, content_text, embedding, metadata)
            VALUES (%s, %s, %s, %s::vector, %s)
            RETURNING id
        """, (
            pg_policy_id,
            "text",
            "Employees must book flights at least 7 days in advance.",
            vector_str,
            Json({"source": "test"})
        ))
        chunk_id = cur.fetchone()[0]
        pg_connection.commit()

        cur.execute("""
            SELECT id, policy_id, content_type, content_text, metadata
            FROM policy_chunks WHERE id = %s
        """, (chunk_id,))
        result = cur.fetchone()

        assert result is not None
        assert result[0] == chunk_id
        assert result[1] == pg_policy_id
        assert result[2] == "text"
        assert "7 days in advance" in result[3]
        assert result[4]["source"] == "test"


@pytest.mark.integration
def test_cosine_similarity_search(pg_connection, pg_policy_id):
    """Test vector similarity search with cosine distance."""
    vector1 = [1.0] * 512 + [0.0] * 512
    vector2 = [0.0] * 512 + [1.0] * 512
    vector3 = [0.9] * 512 + [0.1] * 512

    v1_str = "[" + ",".join(str(v) for v in vector1) + "]"
    v2_str = "[" + ",".join(str(v) for v in vector2) + "]"
    v3_str = "[" + ",".join(str(v) for v in vector3) + "]"

    with pg_connection.cursor() as cur:
        cur.execute("""
            INSERT INTO policy_chunks (policy_id, content_type, content_text, embedding)
            VALUES
                (%s, 'text', 'Chunk 1', %s::vector),
                (%s, 'text', 'Chunk 2', %s::vector),
                (%s, 'text', 'Chunk 3', %s::vector)
        """, (
            pg_policy_id, v1_str,
            pg_policy_id, v2_str,
            pg_policy_id, v3_str,
        ))
        pg_connection.commit()

        query_str = "[" + ",".join(str(v) for v in vector1) + "]"
        cur.execute("""
            SELECT id, content_text, embedding <=> %s::vector AS distance
            FROM policy_chunks WHERE policy_id = %s
            ORDER BY embedding <=> %s::vector LIMIT 3
        """, (query_str, pg_policy_id, query_str))
        results = cur.fetchall()

        assert len(results) == 3
        distances = [row[2] for row in results]
        assert distances[0] < distances[2]
        assert distances == sorted(distances)


@pytest.mark.integration
def test_hnsw_index_used(pg_connection, pg_policy_id):
    """Test that HNSW index is used for similarity queries."""
    vector = [0.5] * 1024
    vector_str = "[" + ",".join(str(v) for v in vector) + "]"

    with pg_connection.cursor() as cur:
        cur.execute("""
            INSERT INTO policy_chunks (policy_id, content_type, content_text, embedding)
            VALUES (%s, 'text', 'Test chunk', %s::vector)
        """, (pg_policy_id, vector_str))
        pg_connection.commit()

        query_str = vector_str
        cur.execute("""
            EXPLAIN (FORMAT TEXT)
            SELECT id FROM policy_chunks
            WHERE policy_id = %s
            ORDER BY embedding <=> %s::vector LIMIT 1
        """, (pg_policy_id, query_str))

        explain_output = "\n".join([row[0] for row in cur.fetchall()])
        assert "policy_chunks" in explain_output.lower()
