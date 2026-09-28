"""Real PostgreSQL tests; model calls are deterministic stubs, not AI quality tests."""
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import ai
from app.db import connect
from app.main import app

pytestmark = pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires initialized PostgreSQL/pgvector")
HEADERS = {"X-Requested-With": "ClauseCompass"}


def register(client):
    response = client.post("/auth/register", json={"email": f"{uuid4()}@example.test", "password": "test-only-long-password"})
    assert response.status_code == 201, response.text


def test_upload_search_and_cross_user_isolation(monkeypatch):
    monkeypatch.setattr(ai, "embeddings", lambda texts: [[1.0] + [0.0] * 767 for _ in texts])
    with TestClient(app, headers=HEADERS) as alice, TestClient(app, headers=HEADERS) as bob:
        register(alice)
        register(bob)
        upload = alice.post("/documents", files={"file": ("agreement.txt", b"Termination requires 30 days notice.")})
        assert upload.status_code == 201, upload.text
        doc_id = upload.json()["id"]
        duplicate = alice.post("/documents", files={"file": ("again.txt", b"Termination requires 30 days notice.")})
        assert duplicate.json()["id"] == doc_id
        query = {"question": "What notice is required?", "document_ids": [doc_id]}
        found = alice.post("/search", json=query)
        assert found.status_code == 200, found.text
        assert "30 days" in found.json()["sources"][0]["text"]
        assert bob.get("/documents").json() == []
        for path in ["/search", "/ask"]:
            assert bob.post(path, json=query).status_code == 404
        assert bob.get(f"/documents/{doc_id}/chunks").status_code == 404
        assert bob.post(f"/documents/{doc_id}/review").status_code == 404
        assert bob.delete(f"/documents/{doc_id}").status_code == 404
        assert alice.delete(f"/documents/{doc_id}").status_code == 204
        assert alice.get(f"/documents/{doc_id}/chunks").status_code == 404
        with connect() as conn:
            assert conn.execute("SELECT count(*) AS n FROM chunks WHERE document_id=%s", (doc_id,)).fetchone()["n"] == 0


def test_failed_embedding_does_not_publish_partial_document(monkeypatch):
    def fail(texts):
        raise ValueError("Model failed")
    monkeypatch.setattr(ai, "embeddings", fail)
    with TestClient(app, headers=HEADERS) as client:
        register(client)
        assert client.post("/documents", files={"file": ("test.txt", b"Contract terms")}).status_code == 422
        assert client.get("/documents").json() == []
