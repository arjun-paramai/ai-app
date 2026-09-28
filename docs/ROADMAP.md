# Turning the starter into strong interview evidence

## Milestone 1 — Reproducible demonstration

- Run Docker and both local models; record a successful upload-to-answer session.
- Confirm GitHub Actions passes the real PostgreSQL tests.
- Run the retrieval evaluator and commit dated results with model digest, machine specs and corpus version.
- Record a two-minute walkthrough showing a correct citation, a comparison, and an unsupported question.
- Add screenshots from the running application. Do not use mock screenshots as proof of an end-to-end system.

Acceptance: a reviewer can clone, follow the README, and reproduce the demonstrated workflow.

## Milestone 2 — Reliable ingestion and retrieval

- Introduce a durable worker queue and persisted states: received, extracting, embedding, ready, failed.
- Make jobs idempotent and retryable, including model/version-aware deduplication.
- Preserve originals in private object storage and add an authenticated PDF viewer with page highlights.
- Add OCR with explicit extraction coverage; test multi-column pages and tables.
- Add schema migrations and model-version migrations.
- Compare fixed windows with clause-aware chunking; benchmark hybrid lexical/vector retrieval and reranking before choosing them.

Acceptance: worker crashes, duplicate uploads, scanned pages, and provider timeouts have tested outcomes.

## Milestone 3 — AI quality with evidence

- Build a larger synthetic corpus with relevant distractors, answerable and unanswerable questions, and gold supporting passages.
- Measure retrieval recall, reciprocal rank, citation support, abstention precision/recall, and p50/p95 latency.
- Evaluate prompt injection and misleading references within contracts.
- Compare at least two generation models on the same held-out set.
- Add long-document map/reduce extraction with coverage accounting and evidence-preserving merging.
- Add deterministic clause alignment and textual diffs alongside semantic comparison.

Acceptance: publish measured results and failures, not an invented accuracy percentage.

## Milestone 4 — Hosted production engineering

- Deploy one cloud target, AWS or Azure, using infrastructure as code.
- Integrate managed identity, organization roles, RLS, private networking, secrets rotation and encrypted storage.
- Separate migrations from runtime permissions.
- Add a gated deployment workflow, smoke checks, rollback, structured metrics, alerts, and a restore drill.
- Document actual operating cost from the chosen region and inference setup.

Acceptance: a live synthetic-data demo, CI/CD evidence, an architecture diagram, and a tested rollback.

## Interview explanation

Explain why exact retrieval is sufficient for the small corpus, why comparison retrieves independently from each document, why citation validation is weaker than factual entailment, and why synchronous ingestion is a deliberate starter limitation. Describe what you personally changed and measured. Treat generated scaffolding as a starting point for understanding and ownership.

After verification, a defensible resume bullet is:

> Built a React and FastAPI contract-review application with PDF/DOCX ingestion, PostgreSQL vector search, evidence-linked RAG, structured extraction, and cross-account access tests.

Add deployment, quality, scale, or latency claims only after measuring them.
