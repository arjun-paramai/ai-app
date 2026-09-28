import json
import httpx
import pytest

from app import ai


def mock_provider(monkeypatch, payload):
    real_client = httpx.Client
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    monkeypatch.setattr(ai.httpx, "Client", lambda **kwargs: real_client(transport=transport, **kwargs))


def test_fabricated_citation_rejected(monkeypatch):
    mock_provider(monkeypatch, {"message": {"content": json.dumps({"claims": [{"text": "Term is one year", "source_ids": [999]}], "insufficient_evidence": False})}})
    with pytest.raises(ValueError, match="outside"):
        ai.generate("Term?", [{"id": 1, "name": "a.txt", "page": 1, "text": "Term is one year"}], ai.Answer)


def test_empty_answer_abstains(monkeypatch):
    mock_provider(monkeypatch, {"message": {"content": '{"claims": [], "insufficient_evidence": false}'}})
    assert ai.generate("Term?", [], ai.Answer)["insufficient_evidence"] is True


def test_embedding_dimension_mismatch_rejected(monkeypatch):
    mock_provider(monkeypatch, {"embeddings": [[0.1, 0.2]]})
    with pytest.raises(ValueError, match="768"):
        ai.embeddings(["test"])
