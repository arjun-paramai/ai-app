"""Run against a live Compose stack with real embeddings; creates and cleans fixture documents."""
import argparse
import json
from pathlib import Path
import time
from uuid import uuid4

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://localhost:8080/api")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
cases = json.loads((root / "evals/retrieval.json").read_text())
with httpx.Client(base_url=args.url + "/", timeout=600, headers={"X-Requested-With": "ClauseCompass"}) as client:
    response = client.post("auth/register", json={"email": f"eval-{uuid4()}@example.test", "password": str(uuid4())})
    response.raise_for_status()
    docs = {}
    results = []
    try:
        for filename in sorted({c["document"] for c in cases}):
            response = client.post("documents", files={"file": (filename, (root / "samples" / filename).read_bytes())})
            response.raise_for_status()
            docs[filename] = response.json()["id"]
        for case in cases:
            start = time.perf_counter()
            response = client.post("search", json={"question": case["question"], "document_ids": [docs[case["document"]]]})
            response.raise_for_status()
            sources = response.json()["sources"]
            ranks = [i + 1 for i, s in enumerate(sources) if case["expected_text"].lower() in s["text"].lower()]
            results.append({"question": case["question"], "rank": min(ranks) if ranks else None,
                            "seconds": round(time.perf_counter() - start, 3)})
        hits = [r for r in results if r["rank"]]
        print(json.dumps({"cases": results, "hit_rate_at_5": len(hits)/len(results),
                          "mrr_at_5": sum(1/r["rank"] for r in hits)/len(results),
                          "note": "Small synthetic smoke benchmark; not a legal-domain quality estimate."}, indent=2))
    finally:
        for doc_id in docs.values():
            client.delete(f"documents/{doc_id}").raise_for_status()
        # The temporary account remains; run only against a disposable demo database.
