# Backend job execution

Scheduled work is exposed as one-shot commands so it is not abandoned when a
web request process restarts:

```bash
python -m backend.jobs.cli daily
python -m backend.jobs.cli tuesday
python -m backend.jobs.cli wednesday
python -m backend.jobs.cli thursday
```

The legacy authenticated `/internal/run-*-job` endpoints remain for
compatibility, but execute the same runner to completion and no longer spawn
daemon threads. Production scheduling should invoke the one-shot command from
the platform scheduler/worker and retain its exit status and logs.

The current job functions still use existing email/X integrations and need a
later B5 slice for durable idempotency keys, cross-process locking, provider
timeouts, and persisted run counts.
