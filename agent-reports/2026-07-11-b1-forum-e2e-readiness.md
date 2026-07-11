# B1 browser readiness evidence — 2026-07-11

## Summary

Stabilized the existing `/forum/post` mobile-navigation E2E test by waiting
for the rendered page and network idle before interacting with the hydrated
header. The test previously clicked the server-rendered header before Svelte
hydration had attached the menu handler under the full parallel workload.
This changes test readiness only; no product behavior changed.

## Verification

- Focused test: 1 passed.
- Full Playwright suite: 97 passed.
- Accumulated canonical gate: Python static 169, Playwright 97, integration
  16, legacy E2E 38 passed.
- Canonical logs: `.tmp/test-logs/20260711-003807/`.

## Next step

Keep the readiness assertion while continuing backend modernization; do not
use serialized browser execution to hide concurrency problems.
