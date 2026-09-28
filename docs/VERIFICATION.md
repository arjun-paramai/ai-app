# Verification record

Verified locally on September 28, 2026.

| Check | Result |
|---|---|
| Python tests after dependency updates | 12 passed; 2 database integration tests skipped |
| TypeScript compiler | Passed |
| Vite production build | Passed with Vite 6.4.3 |
| Browser load | Built frontend opened to the expected account screen |
| npm dependency audit | No known vulnerabilities reported, including dev dependencies |
| Python environment dependency audit | No known vulnerabilities reported after upgrades |
| Python dependency compatibility | `pip check` passed |
| Docker/database integration | Not run: local Docker engine unavailable |
| Live model ingestion/RAG | Not run; no AI-quality or latency results claimed |
| GitHub Actions / image publishing | Workflows provided, not executed in GitHub |
| AWS deployment | Design only; not provisioned or verified |

The local filesystem sandbox required `vite build --configLoader runner` to avoid ancestor-directory discovery while loading the Vite configuration. The standard build script remains appropriate for an ordinary checkout and the container build.

The Python test run reports a Starlette deprecation warning for its httpx-backed TestClient. Tests pass; a future migration to the recommended replacement test transport remains follow-up work.

Dependency audits reflect the registry advisory data available at verification time. They are not a security certification. Container images were not built or scanned in this environment.

Before presenting the project as an end-to-end working demo, run Docker Compose and the real-model evaluator, verify cross-account isolation in CI, and replace this record with the measured results.
