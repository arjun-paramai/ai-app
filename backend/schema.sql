CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE users (
 id uuid PRIMARY KEY, email text UNIQUE NOT NULL, password_hash text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE documents (
 id uuid PRIMARY KEY, owner_id uuid NOT NULL REFERENCES users(id), name text NOT NULL,
 sha256 text NOT NULL, embedding_model text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(owner_id, sha256)
);
CREATE INDEX documents_owner ON documents(owner_id);
CREATE TABLE chunks (
 id bigserial PRIMARY KEY, document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
 page integer NOT NULL, text text NOT NULL, embedding vector(768) NOT NULL
);
CREATE INDEX chunks_document ON chunks(document_id);
-- Exact cosine search is intentional for the small portfolio corpus.
-- Measure filtered recall before introducing an approximate HNSW index.
