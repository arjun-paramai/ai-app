# AWS deployment design — not yet deployed

This document is a target architecture and implementation checklist. The repository currently supplies local Compose, CI tests/builds, and a manual GHCR publishing workflow. It does not provision AWS infrastructure or claim a successful cloud deployment.

## Proposed topology

Use an HTTPS Application Load Balancer in public subnets, with the web proxy and FastAPI containers on ECS Fargate in private subnets. Use RDS PostgreSQL with the vector extension after verifying support for the selected engine version. Put original documents in a private encrypted S3 bucket once original-file retention is implemented. Send container logs and application metrics to CloudWatch. Use Secrets Manager for database credentials and signing keys, and Cognito or another OIDC provider for hosted authentication.

The local Ollama process is not included in the API image. For hosted inference, either operate it on a separate private compute service sized for the chosen model, or implement a managed model provider adapter. Verify model availability, API behavior, data residency and embedding dimensions before switching providers. Fargate API tasks alone do not provide the local inference service.

## Concrete release sequence

1. Add Terraform for networking, ECS, load balancing/TLS, RDS, secrets, IAM and log groups. Estimate and approve cloud costs before applying it.
2. Create a migration role and a least-privilege application role. Replace one-time initialization SQL with versioned migrations.
3. Add organization authorization and database RLS, managed login, secure cookies and production rate limits.
4. Configure inference in the private network; test dimensions, model versioning, structured output validation and timeout handling.
5. Build images from a tested commit and scan them. The provided publish workflow tags images by commit SHA; retain the image digest for deployment.
6. Use GitHub OIDC to obtain a scoped AWS deployment role. Gate production with a GitHub environment and approvals appropriate to the owner.
7. Run migrations as a separate task, update the ECS service, and wait for health checks. Add a model readiness smoke check separately from database readiness.
8. Execute a synthetic upload/search/answer/delete smoke test. Check that request IDs correlate through logs and that no raw document content is logged.
9. Roll back to the prior image digest on failed smoke checks. Use backward-compatible schema changes so rollback remains possible.
10. Test backup restoration and define deletion/retention behavior before accepting real customer data.

## Environment contract

| Variable | Meaning |
|---|---|
| `DATABASE_URL` | Private PostgreSQL connection URL; add verified TLS settings for hosted RDS |
| `JWT_SECRET` | Temporary local-auth signing key; replace local auth for production |
| `COOKIE_SECURE` | Set `true` with HTTPS |
| `OLLAMA_URL` | Private inference endpoint |
| `EMBED_MODEL` | Model consistent with stored 768-dimensional vectors |
| `CHAT_MODEL` | Model tested for structured review and answer output |

The current web proxy expects the API hostname `api`. An ECS topology must provide that name through service discovery or generate proxy configuration for the deployed endpoint. Local Compose values are not cloud configuration.

## Operational acceptance criteria

- Database, inference, and worker failures are visible and recoverable.
- Restore and rollback are exercised, not only documented.
- Published p95 latency and cost numbers come from reproducible measurements.
- No production secrets are stored in GitHub repository files, Docker build args, or browser bundles.
- Public demo accounts see synthetic data only and have upload/request quotas.
