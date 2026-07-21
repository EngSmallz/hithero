# Azure App Service preparation

This is a deployment-preparation reference, not an Azure rollout runbook. The
current application must be deployable and verifiable with local/test-safe
providers before real Azure credentials are enabled.

## Deployment shape to decide

The UI is a SvelteKit server application (SSR loads and server actions), and
the API is FastAPI. Treat them as separate runtimes:

- a Node-compatible SvelteKit deployment;
- a Python FastAPI deployment;
- one public routing/origin plan that sends browser page requests to SvelteKit
  and API requests to FastAPI while preserving cookies and forwarded headers.

The frontend currently uses `@sveltejs/adapter-auto`; select and verify the
explicit production adapter and start command before deployment. Do not make
the legacy FastAPI HTML layer the production fallback.

## App Service configuration inventory

Configure these through App Service settings or managed secret storage, never
in tracked files:

| Purpose | Configuration |
| --- | --- |
| Application mode | `APP_ENV`, `SECRET_KEY`, `PROVIDER_TIMEOUT_SECONDS` |
| Database | `DATABASE_URL`, or the configured SQL Server connection variables |
| Browser/API boundary | `PUBLIC_BACKEND_ORIGIN`, `CORS_ALLOW_ORIGINS` |
| Azure Communication Services email | `AZURE_EMAIL_CONNECTION_STRING`, `AZURE_EMAIL_SENDER` |
| reCAPTCHA | `SERVER_KEY_CAPTCHA` |
| X publishing, if retained | `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` |
| Scheduled job trigger | the configured cron-job authorization secret |

The extracted Azure provider is `backend/integrations/providers.py`.
`backend/jobs/legacy.py` retains the existing notification workflows. Keep
those modules; do not copy them back into `app.py`.

## Pre-deployment proof

1. Build and start the chosen SvelteKit production runtime locally or in CI.
2. Start FastAPI with production-like proxy/origin settings and confirm cookie,
   CSRF, redirect, SSR, and API behavior.
3. Run the manual acceptance gate in `GOLDEN_TARGET.md` and
   `scripts/run-all-tests.sh`.
4. Use non-production Azure credentials or provider mocks for a smoke email,
   reCAPTCHA rejection, and provider-failure response.
5. Only then configure production App Service secrets, deploy to a non-public
   slot/environment, and repeat health, readiness, auth, public-page, and
   email smoke checks.

## Out of scope for this note

Creating Azure resources, applying production migrations, rotating secrets,
and switching traffic require an explicit deployment task and approval.
