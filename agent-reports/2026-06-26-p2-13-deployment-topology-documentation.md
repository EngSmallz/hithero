# P2-13 Deployment Topology Documentation

## Summary

- What changed: Added deployment topology documentation covering local and production service shape, environment variables, cookie/CORS behavior, reverse-proxy assumptions, static asset ownership, health probes, and verification gates.
- Why it changed: P2-13 requires deployment assumptions to be explicit instead of living only in code and agent memory.
- Ticket(s): `ticket/P2-13-deployment-topology-documentation.md`

## Files Touched

- `docs/deployment-topology.md`
- `docs/local-dev.md`
- `README.md`

## Implementation Notes

- Production recommendation is one public HTTPS origin with SvelteKit and FastAPI behind a reverse proxy.
- The doc calls out shared-prefix routing risk for `/profile/*` and `/forum/*`, where browser routes and API endpoints coexist.
- No dedicated `/healthz` endpoint exists yet, so the doc lists current lightweight probes and names a future dedicated health endpoint as an operational improvement.

## Verification

Commands run:

```bash
make dev-backend
curl -s -o /tmp/hithero-backend-probe.out -w "%{http_code}" http://127.0.0.1:8000/
make dev-frontend
curl -s -o /tmp/hithero-frontend-probe.out -w "%{http_code}" http://127.0.0.1:5173/
scripts/run-all-tests.sh --quick
```

Results:

- Passed: documented backend startup served `/` with HTTP 200, then shut down cleanly.
- Passed: documented frontend startup served `/` with HTTP 200, then shut down.
- Passed: quick gate passed Svelte check, frontend lint, and Python static tests.

## Known Issues

- The frontend dev probe logged an expected backend `ECONNREFUSED` during shutdown because the backend was intentionally stopped before the frontend probe. The frontend still served HTTP 200; normal local use should run both commands side by side.

## Next Best Step

- Proceed to P2-14 Manual Responsive QA Pass.
