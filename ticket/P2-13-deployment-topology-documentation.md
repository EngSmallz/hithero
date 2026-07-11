# P2-13: Document Deployment Topology

## Problem

The final SvelteKit + FastAPI deployment topology affects cookies, CORS, origins, health checks, canonical URLs, and reverse proxy rules. The modernization should not end with this knowledge living only in heads.

## Scope

Document the intended deployment model:

- SvelteKit and FastAPI hosted together behind one reverse proxy, or separately.
- Required environment variables.
- Cookie/session expectations.
- CORS settings.
- Backend origin used by SvelteKit.
- Canonical public origin.
- Health check endpoints.
- Static asset ownership.

## Acceptance Criteria

- Local and production environment assumptions are documented.
- Required variables are listed with safe examples.
- Cookie/CORS behavior is explicit.
- Reverse proxy or hosting assumptions are clear enough for deployment.
- The docs point to the canonical test gate.

## Verification

- Review `README.md`, `docs/local-dev.md`, and modernization docs.
- Run documented local startup commands.
- Run documented verification command.
