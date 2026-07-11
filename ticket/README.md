# Modernization Completion Tickets

This directory tracks the remaining modernization work needed to make the SvelteKit + FastAPI migration effectively complete.

The core migration is substantially in place. These tickets focus on the edge integrity needed before calling the effort done: progressive form behavior, reliable parallel test execution, legacy cleanup, SEO/indexing policy, security hardening, and final operational polish.

## Priority Order

### P0 - Completion Blockers

1. [P0-01 Forum New Progressive Create Flow](./P0-01-forum-new-progressive-create-flow.md)
2. [P0-02 Parallel E2E Determinism](./P0-02-parallel-e2e-determinism.md)
3. [P0-03 Canonical Modernization Gate](./P0-03-canonical-modernization-gate.md)

### P1 - Edge Integrity

4. [P1-04 Svelte Form Fallback Audit](./P1-04-svelte-form-fallback-audit.md)
5. [P1-05 Forum DB Session Error Paths](./P1-05-forum-db-session-error-paths.md)
6. [P1-06 Legacy Route Cleanup Plan](./P1-06-legacy-route-cleanup-plan.md)
7. [P1-07 SEO And Indexing Policy Lock](./P1-07-seo-and-indexing-policy-lock.md)
8. [P1-08 Forum HTML Safety Contract](./P1-08-forum-html-safety-contract.md)
9. [P1-09 Teacher Directory Pagination Coverage](./P1-09-teacher-directory-pagination-coverage.md)
10. [P1-10 Critical Flow Slow JS Coverage](./P1-10-critical-flow-slow-js-coverage.md)

### P2 - Finish Quality

11. [P2-11 Normalize API Client Usage](./P2-11-normalize-api-client-usage.md)
12. [P2-12 Clean Test Warning Noise](./P2-12-clean-test-warning-noise.md)
13. [P2-13 Deployment Topology Documentation](./P2-13-deployment-topology-documentation.md)
14. [P2-14 Manual Responsive QA Pass](./P2-14-manual-responsive-qa-pass.md)
15. [P2-15 Final Dead Code Removal Pass](./P2-15-final-dead-code-removal-pass.md)

## 99% Complete Bar

The modernization effort should be considered 99% complete when:

- P0 and P1 tickets are complete.
- `scripts/run-all-tests.sh` passes repeatedly from a clean checkout.
- Parallel E2E/integration execution is deterministic without reducing real backend concurrency coverage.
- Legacy route, sitemap, robots/noindex, and deployment topology decisions are documented.
- Any remaining P2 work is polish rather than correctness, security, migration, or release confidence work.
