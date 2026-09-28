import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Compass,
  FileText,
  Upload,
  Search,
  ArrowUpRight,
  LogOut,
  ShieldCheck,
  Trash2,
  X,
  Sparkles,
} from "lucide-react";
import "./style.css";

type Doc = { id: string; name: string; chunks: number; created_at: string };
type Source = {
  id: number;
  name: string;
  page: number;
  text: string;
  score?: number;
};
type Claim = { text: string; source_ids: number[] };
type Fact = { category: string; value: string; source_ids: number[] };
type Result = {
  claims?: Claim[];
  summary?: Claim[];
  facts?: Fact[];
  risks?: Claim[];
  insufficient_evidence?: boolean;
};
type Evidence = { result?: Result; sources: Source[]; scope?: string };

async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const form = body instanceof FormData;
  const response = await fetch(`/api${path}`, {
    method,
    credentials: "same-origin",
    headers: {
      "X-Requested-With": "ClauseCompass",
      ...(!form && body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? (form ? body : JSON.stringify(body)) : undefined,
  });
  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: `Request failed (${response.status})` }));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : "Please check your input.",
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

function App() {
  const [user, setUser] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);
  const [register, setRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [docs, setDocs] = useState<Doc[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [source, setSource] = useState<Source | null>(null);
  const [title, setTitle] = useState("");
  async function refresh() {
    setDocs(await api<Doc[]>("/documents"));
  }
  useEffect(() => {
    api<{ email: string }>("/auth/me")
      .then((u) => setUser(u.email))
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);
  useEffect(() => {
    if (user) refresh().catch((e) => setError(e.message));
  }, [user]);
  async function run(label: string, fn: () => Promise<void>) {
    setBusy(label);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setBusy("");
    }
  }
  function toggle(id: string) {
    setSelected((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id)
        : [...prev.slice(-1), id],
    );
    setEvidence(null);
    setSource(null);
  }
  async function query(kind: "ask" | "search", value = question) {
    if (!value.trim() || !selected.length) return;
    await run(
      kind === "ask" ? "Reading the evidence…" : "Searching passages…",
      async () => {
        const result = await api<Evidence>(`/${kind}`, "POST", {
          question: value,
          document_ids: selected,
        });
        setTitle(value);
        setEvidence(result);
        setSource(null);
      },
    );
  }
  function citations(ids: number[]) {
    return ids.map((id) => (
      <button
        className="citation"
        key={id}
        onClick={() =>
          setSource(evidence?.sources.find((s) => s.id === id) ?? null)
        }
        aria-label={`Open source ${id}`}
      >
        [{id}]
      </button>
    ));
  }
  function claims(items: Claim[] = []) {
    return items.map((c, i) => (
      <p className="claim" key={i}>
        {c.text} {citations(c.source_ids)}
      </p>
    ));
  }

  if (checking) return <div className="loading">Opening your workspace…</div>;
  if (!user)
    return (
      <div className="auth">
        <div className="auth-story">
          <div className="brand">
            <Compass /> ClauseCompass
          </div>
          <span className="eyebrow">CONTRACT INTELLIGENCE</span>
          <h1>
            Read between
            <br />
            the clauses.
          </h1>
          <p>
            Find the terms that matter. Ask better questions.
            <br />
            Keep the evidence in view.
          </p>
          <div className="auth-proof">
            <ShieldCheck /> Private workspace · Cited answers · Local AI
          </div>
        </div>
        <form
          className="auth-form"
          onSubmit={(e) => {
            e.preventDefault();
            run("Signing in…", async () => {
              const u = await api<{ email: string }>(
                `/auth/${register ? "register" : "login"}`,
                "POST",
                { email, password },
              );
              setUser(u.email);
              setPassword("");
            });
          }}
        >
          <span className="eyebrow">YOUR REVIEW DESK</span>
          <h2>{register ? "Create your workspace" : "Welcome back"}</h2>
          <p>Bring clarity to your next agreement.</p>
          <label>
            Email
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              required
              minLength={12}
              maxLength={128}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={register ? "new-password" : "current-password"}
            />
          </label>
          <small>Use at least 12 characters.</small>
          {error && (
            <div role="alert" className="error">
              {error}
            </div>
          )}
          <button className="primary" disabled={!!busy}>
            {busy || (register ? "Create account" : "Open workspace")}{" "}
            <ArrowUpRight size={17} />
          </button>
          <button
            type="button"
            className="text-button"
            onClick={() => setRegister(!register)}
          >
            {register
              ? "Already have an account? Sign in"
              : "New here? Create an account"}
          </button>
        </form>
      </div>
    );

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <Compass /> ClauseCompass
        </div>
        <div className="workspace">
          <span className="avatar">W</span>
          <div>
            My workspace<small>Personal review desk</small>
          </div>
        </div>
        <div className="nav-active">
          <FileText size={18} /> Documents <span>{docs.length}</span>
        </div>
        <div className="sidebar-note">
          <ShieldCheck size={20} />
          <p>Evidence comes first.</p>
          <small>
            Every generated finding links to a passage you can verify.
          </small>
        </div>
        <button
          className="logout"
          disabled={!!busy}
          onClick={() =>
            run("Signing out…", async () => {
              await api("/auth/logout", "POST");
              setUser(null);
              setDocs([]);
              setSelected([]);
              setEvidence(null);
              setSource(null);
            })
          }
        >
          <LogOut size={16} />
          <span>{user}</span>
        </button>
      </aside>
      <main>
        <header>
          <span>
            Workspace <span className="slash">/</span> Contract library
          </span>
          <span className="status">
            <i /> Local AI workspace
          </span>
        </header>
        <section className="page-heading">
          <div>
            <span className="eyebrow">FROM DOCUMENTS TO DECISIONS</span>
            <h1>
              Your contract library<span>.</span>
            </h1>
            <p>
              Explore agreements, surface key terms, and follow the evidence.
            </p>
          </div>
          <label className={`upload primary ${busy ? "disabled" : ""}`}>
            <Upload size={17} /> Upload document
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              disabled={!!busy}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f)
                  run("Extracting and indexing…", async () => {
                    const body = new FormData();
                    body.append("file", f);
                    const d = await api<Doc>("/documents", "POST", body);
                    await refresh();
                    setSelected([d.id]);
                    setEvidence(null);
                  });
                e.target.value = "";
              }}
            />
          </label>
        </section>
        <div className="overview">
          <div>
            <span className="metric">
              {docs.length.toString().padStart(2, "0")}
            </span>
            <span>Documents indexed</span>
          </div>
          <div>
            <span className="metric">
              {docs
                .reduce((n, d) => n + Number(d.chunks), 0)
                .toString()
                .padStart(2, "0")}
            </span>
            <span>Searchable passages</span>
          </div>
          <div>
            <span className="metric">
              {selected.length === 2 ? "Compare" : "Review"}
            </span>
            <span>
              {selected.length === 2
                ? "Two agreements selected"
                : "Select up to two agreements"}
            </span>
          </div>
        </div>
        {error && (
          <div className="error" role="alert">
            {error}
            <button onClick={() => setError("")} aria-label="Dismiss error">
              <X size={16} />
            </button>
          </div>
        )}
        <div className="content-grid">
          <section className="library">
            <div className="section-title">
              <h2>All documents</h2>
              <span>PDF / DOCX / TXT</span>
            </div>
            {docs.length === 0 ? (
              <div className="empty">
                <FileText size={36} />
                <h3>A clearer picture starts here.</h3>
                <p>
                  Upload a contract to search its terms and ask questions with
                  cited answers.
                </p>
                <small>
                  Try either synthetic agreement in the repository’s samples
                  folder.
                </small>
              </div>
            ) : (
              <div className="doc-list">
                {docs.map((d) => (
                  <div
                    className={`doc-card ${selected.includes(d.id) ? "selected" : ""}`}
                    key={d.id}
                  >
                    <button
                      className="doc-select"
                      disabled={!!busy}
                      onClick={() => toggle(d.id)}
                      aria-pressed={selected.includes(d.id)}
                    >
                      <span className="file-icon">
                        <FileText size={23} />
                      </span>
                      <span className="doc-info">
                        <strong>{d.name}</strong>
                        <small>
                          {d.chunks} passages ·{" "}
                          {new Date(d.created_at).toLocaleDateString()}
                        </small>
                      </span>
                      <span className="check">
                        {selected.includes(d.id) ? "✓" : ""}
                      </span>
                    </button>
                    <button
                      className="delete"
                      disabled={!!busy}
                      aria-label={`Delete ${d.name}`}
                      onClick={() => {
                        if (
                          window.confirm(
                            `Delete ${d.name} and its indexed passages?`,
                          )
                        )
                          run("Deleting…", async () => {
                            await api(`/documents/${d.id}`, "DELETE");
                            setSelected((s) => s.filter((id) => id !== d.id));
                            setEvidence(null);
                            setSource(null);
                            await refresh();
                          });
                      }}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            <div className="library-foot">
              Select one document to review, or two to compare.
            </div>
          </section>
          <section className="assistant">
            <div className="section-title">
              <h2>
                <Sparkles size={18} /> Ask your contracts
              </h2>
              <span>{selected.length} SELECTED</span>
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                query("ask");
              }}
            >
              <label className="sr-only" htmlFor="question">
                Question about selected contracts
              </label>
              <textarea
                id="question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="What are the termination rights and notice periods?"
                maxLength={1000}
              />
              <div className="query-actions">
                <button
                  type="button"
                  className="secondary"
                  disabled={
                    !!busy || !selected.length || question.trim().length < 3
                  }
                  onClick={() => query("search")}
                >
                  <Search size={15} /> Search
                </button>
                <button
                  className="primary"
                  disabled={
                    !!busy || !selected.length || question.trim().length < 3
                  }
                >
                  Ask with evidence <ArrowUpRight size={16} />
                </button>
              </div>
            </form>
            <div className="suggestions">
              {[
                "What payment obligations apply?",
                "What risks need human review?",
              ].map((q) => (
                <button
                  key={q}
                  disabled={!!busy || !selected.length}
                  onClick={() => {
                    setQuestion(q);
                    query("ask", q);
                  }}
                >
                  {q}
                </button>
              ))}
              <button
                disabled={!!busy || selected.length !== 1}
                onClick={() =>
                  run("Reviewing all passages…", async () => {
                    setEvidence(
                      await api<Evidence>(
                        `/documents/${selected[0]}/review`,
                        "POST",
                      ),
                    );
                    setTitle("Agreement review");
                    setSource(null);
                  })
                }
              >
                Summarize & extract key terms
              </button>
            </div>
            <div className="ai-note">
              AI findings are draft observations. Verify cited passages before
              relying on them.
            </div>
          </section>
        </div>
        {busy && (
          <div className="busy" role="status">
            <span className="spinner" />
            {busy}
          </div>
        )}
        {evidence && (
          <section className="results">
            <div className="section-title">
              <h2>{title}</h2>
              <span>{evidence.scope || "SEMANTIC SEARCH"}</span>
            </div>
            {evidence.result?.insufficient_evidence && (
              <p className="empty-answer">
                The retrieved passages do not contain enough evidence to answer
                confidently.
              </p>
            )}
            {claims(evidence.result?.claims)}
            {evidence.result?.summary && (
              <>
                <h3>Summary</h3>
                {claims(evidence.result.summary)}
              </>
            )}
            {evidence.result?.facts && (
              <>
                <h3>Key terms</h3>
                <div className="facts">
                  {evidence.result.facts.map((f, i) => (
                    <div key={i}>
                      <span>{f.category}</span>
                      <p>
                        {f.value} {citations(f.source_ids)}
                      </p>
                    </div>
                  ))}
                </div>
              </>
            )}
            {evidence.result?.risks && (
              <>
                <h3>Issues for human review</h3>
                {claims(evidence.result.risks)}
                {!evidence.result.risks.length && (
                  <p>
                    No issues were returned. This is not a finding that the
                    agreement is risk-free.
                  </p>
                )}
              </>
            )}
            <h3>Source passages</h3>
            <div className="sources">
              {evidence.sources.map((s) => (
                <button key={s.id} onClick={() => setSource(s)}>
                  <span>
                    [{s.id}] {s.name} ·{" "}
                    {s.name.toLowerCase().endsWith(".pdf") ? "Page" : "Section"}{" "}
                    {s.page}
                  </span>
                  <p>{s.text.slice(0, 180)}…</p>
                  <small>
                    Inspect evidence <ArrowUpRight size={13} />
                  </small>
                </button>
              ))}
            </div>
          </section>
        )}
        <footer>
          CLAUSECOMPASS <span>Contract intelligence, with a paper trail.</span>
        </footer>
      </main>
      {source && (
        <div className="drawer-overlay" onClick={() => setSource(null)}>
          <section
            className="drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Source passage"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="close"
              autoFocus
              onClick={() => setSource(null)}
              aria-label="Close source"
            >
              <X />
            </button>
            <span className="eyebrow">SOURCE EVIDENCE · [{source.id}]</span>
            <h2>{source.name}</h2>
            <p className="source-page">
              {source.name.toLowerCase().endsWith(".pdf")
                ? "Page"
                : "Extracted section"}{" "}
              {source.page}
            </p>
            <blockquote>{source.text}</blockquote>
            <small>
              Original extracted text. PDF page numbers are preserved; DOCX and
              TXT use section 1.
            </small>
          </section>
        </div>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
