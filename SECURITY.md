# Security scope

This is a local portfolio starter using synthetic contracts. Production controls are explicitly incomplete.

## Implemented controls

- Passwords use Argon2; sessions are signed, expire after eight hours, and live in HttpOnly SameSite=Strict cookies.
- The API requires a custom header for mutations. No cross-origin allowlist is enabled; the UI and API share an origin through Nginx.
- Document access filters by authenticated account ID. Tests exercise direct cross-user requests. No user-controlled owner ID is accepted.
- Upload size is bounded at the reverse proxy and API; text length and PDF page count are bounded after parsing. DOCX expanded size is checked before parsing.
- The browser renders model outputs as plain React text, never raw HTML.
- The model receives document text as untrusted data and is asked to ignore embedded instructions. Citation IDs must belong to the retrieved evidence. This does not prove factual support or prevent all prompt injection.
- Logs contain request IDs, method, path, status and duration, not document content or passwords. Dependency/provider logs should also be reviewed before production use.
- Nginx limits authentication requests. API and database ports are private in Compose.

## Threats and remaining work

| Threat | Remaining production control |
|---|---|
| Malicious PDF or resource exhaustion | Isolated ingestion worker with CPU/memory/time limits, malware scanning, parser updates |
| Account takeover | Managed OIDC, MFA, breached-password checks, recovery, server-side session revocation |
| Cross-tenant access after a coding mistake | Database RLS with non-owner/non-bypass runtime role; organization membership tests |
| Data loss | Encrypted storage/backups, retention policy, restore drills, auditable deletion |
| Model injection or hallucination | Adversarial evals, claim-to-passage support evaluation, restricted model network access |
| Provider outage or expensive requests | Queue, quotas, bounded retries, circuit breaker, metrics and alerting |
| Dependency compromise | Locked dependencies, scheduled audits, image scanning, signed artifacts and SBOMs |

Set `COOKIE_SECURE=true` behind HTTPS in a cloud environment. Changing cookie settings alone does not make the starter production-ready. Sessions cannot currently be revoked server-side before expiry. Logout removes the browser cookie only.

The Compose database account is an initialization owner, appropriate only to this isolated local demo. Create separate migration and restricted runtime roles before hosted use. RLS owners and bypass roles need special care.

If publishing publicly, enable GitHub private vulnerability reporting rather than asking reporters to post exploit details in public issues.
