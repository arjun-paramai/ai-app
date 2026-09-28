import hashlib
import json
import logging
import time
from uuid import UUID, uuid4

import httpx
import numpy as np
import psycopg
from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import ai
from .auth import current_user, passwords, token
from .config import settings
from .db import connect
from .ingestion import chunk_pages, extract_pages

app = FastAPI(title="ClauseCompass", version="0.1.0")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clausecompass")


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id, started = str(uuid4()), time.perf_counter()
    # Custom header + same-origin proxy prevents browser cross-site mutations.
    if request.method in {"POST", "DELETE", "PUT", "PATCH"} and request.headers.get("x-requested-with") != "ClauseCompass":
        return JSONResponse({"detail": "Missing request header."}, status_code=403)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    logger.info(json.dumps({"request_id": request_id, "method": request.method,
                           "path": request.url.path, "status": response.status_code,
                           "duration_ms": round((time.perf_counter() - started) * 1000)}))
    return response


@app.exception_handler(httpx.HTTPError)
async def provider_error(request, exc):
    return JSONResponse({"detail": "AI provider unavailable. Check Ollama and installed models."}, status_code=502)


@app.exception_handler(ValueError)
async def validation_error(request, exc):
    return JSONResponse({"detail": "Processing failed validation. Check document input or model output."}, status_code=422)


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=12, max_length=128)


class Query(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    document_ids: list[UUID] = Field(min_length=1, max_length=2)


def set_session(response: Response, uid):
    response.set_cookie("session", token(str(uid)), httponly=True, samesite="strict",
                        secure=settings.cookie_secure, max_age=8 * 3600, path="/")


@app.post("/auth/register", status_code=201)
def register(body: Credentials, response: Response):
    uid = uuid4()
    try:
        with connect() as conn:
            conn.execute("INSERT INTO users(id,email,password_hash) VALUES (%s,%s,%s)",
                         (uid, body.email.lower(), passwords.hash(body.password)))
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "Unable to create this account.")
    set_session(response, uid)
    return {"email": body.email.lower()}


@app.post("/auth/login")
def login(body: Credentials, response: Response):
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=%s", (body.email.lower(),)).fetchone()
    if not row or not passwords.verify(body.password, row["password_hash"]):
        raise HTTPException(401, "Invalid email or password.")
    set_session(response, row["id"])
    return {"email": row["email"]}


@app.post("/auth/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie("session", path="/")


@app.get("/auth/me")
def me(uid: UUID = Depends(current_user)):
    with connect() as conn:
        row = conn.execute("SELECT email FROM users WHERE id=%s", (uid,)).fetchone()
    if not row:
        raise HTTPException(401, "Account unavailable.")
    return row


@app.get("/health")
def health():
    with connect() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/documents")
def documents(uid: UUID = Depends(current_user)):
    with connect() as conn:
        return conn.execute("SELECT d.id,d.name,d.created_at,count(c.id) AS chunks FROM documents d "
                            "LEFT JOIN chunks c ON c.document_id=d.id WHERE d.owner_id=%s "
                            "GROUP BY d.id ORDER BY d.created_at DESC", (uid,)).fetchall()


@app.post("/documents", status_code=201)
def upload(file: UploadFile = File(...), uid: UUID = Depends(current_user)):
    data = file.file.read(10_000_001)
    if len(data) > 10_000_000:
        raise HTTPException(413, "Maximum upload size is 10 MB.")
    name = (file.filename or "upload.txt").replace("\\", "/").split("/")[-1][:200]
    try:
        chunks = chunk_pages(extract_pages(name, data))
    except Exception as exc:
        raise HTTPException(422, "Could not extract document text. Use an unencrypted text PDF, DOCX, or UTF-8 TXT.") from exc
    if not chunks:
        raise HTTPException(422, "Document contains no usable text.")
    digest = hashlib.sha256(data).hexdigest()
    with connect() as conn:
        previous = conn.execute("SELECT id,name FROM documents WHERE owner_id=%s AND sha256=%s", (uid, digest)).fetchone()
    if previous:
        return previous
    vectors = ai.embeddings(["search_document: " + c["text"] for c in chunks])
    doc_id = uuid4()
    try:
        with connect() as conn:
            conn.execute("INSERT INTO documents(id,owner_id,name,sha256,embedding_model) VALUES (%s,%s,%s,%s,%s)",
                         (doc_id, uid, name, digest, settings.embed_model))
            with conn.cursor() as cur:
                cur.executemany("INSERT INTO chunks(document_id,page,text,embedding) VALUES (%s,%s,%s,%s)",
                                [(doc_id, c["page"], c["text"], np.array(v)) for c, v in zip(chunks, vectors, strict=True)])
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "Document already uploaded. Refresh the document list.")
    return {"id": doc_id, "name": name, "chunks": len(chunks)}


def owned(conn, ids: list[UUID], uid: UUID):
    rows = conn.execute("SELECT id,embedding_model FROM documents WHERE id=ANY(%s) AND owner_id=%s", (ids, uid)).fetchall()
    if len(rows) != len(set(ids)):
        raise HTTPException(404, "Document unavailable.")
    if any(row["embedding_model"] != settings.embed_model for row in rows):
        raise HTTPException(409, "Embedding model changed. Re-ingest documents before search.")


@app.get("/documents/{doc_id}/chunks")
def document_chunks(doc_id: UUID, uid: UUID = Depends(current_user)):
    with connect() as conn:
        owned(conn, [doc_id], uid)
        return conn.execute("SELECT c.id,c.page,c.text,d.name FROM chunks c JOIN documents d ON d.id=c.document_id "
                            "WHERE d.id=%s AND d.owner_id=%s ORDER BY c.id", (doc_id, uid)).fetchall()


@app.delete("/documents/{doc_id}", status_code=204)
def delete(doc_id: UUID, uid: UUID = Depends(current_user)):
    with connect() as conn:
        row = conn.execute("DELETE FROM documents WHERE id=%s AND owner_id=%s RETURNING id", (doc_id, uid)).fetchone()
        if not row:
            raise HTTPException(404, "Document unavailable.")


def retrieve(body: Query, uid: UUID):
    with connect() as conn:
        owned(conn, body.document_ids, uid)
    vector = np.array(ai.embeddings(["search_query: " + body.question])[0])
    sources = []
    with connect() as conn:
        # Retrieve per document so a comparison cannot crowd out one side.
        for doc_id in dict.fromkeys(body.document_ids):
            sources.extend(conn.execute(
                "SELECT c.id,c.page,c.text,d.name,d.id AS document_id,1-(c.embedding <=> %s) AS score "
                "FROM chunks c JOIN documents d ON d.id=c.document_id "
                "WHERE d.id=%s AND d.owner_id=%s ORDER BY c.embedding <=> %s LIMIT 5",
                (vector, doc_id, uid, vector)).fetchall())
    return sources


@app.post("/search")
def search(body: Query, uid: UUID = Depends(current_user)):
    return {"sources": retrieve(body, uid)}


@app.post("/ask")
def ask(body: Query, uid: UUID = Depends(current_user)):
    sources = retrieve(body, uid)
    task = body.question
    if len(set(body.document_ids)) == 2:
        task = "Compare the two documents on the following question. Cite both sides when supported. " + task
    result = ai.generate(task, sources, ai.Answer)
    return {"result": result, "sources": sources, "scope": "Top 5 retrieved passages per selected document"}


@app.post("/documents/{doc_id}/review")
def review(doc_id: UUID, uid: UUID = Depends(current_user)):
    sources = document_chunks(doc_id, uid)
    if len(sources) > 20:
        raise HTTPException(422, "Full review supports up to 20 chunks. Use focused questions for longer contracts.")
    result = ai.generate("Summarize this agreement and extract parties, dates, obligations, important clauses and potential risks.", sources, ai.Review)
    return {"result": result, "sources": sources, "scope": "All extracted passages"}
