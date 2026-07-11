# Production database migration policy

Production startup does not create tables. Schema changes are applied through
the Alembic revisions under `migrations/`:

```bash
alembic -c alembic.ini upgrade head
```

The first revision is a reviewed baseline marker, not an inferred production
DDL script. Before stamping it, operations must capture the SQL Server schema,
compare legacy names and constraints with `backend/db/models.py`, take a backup,
and rehearse the rollout against a production-shaped copy. SQLite tests remain
useful for repository behavior, but SQL Server verification is required when
types, indexes, constraints, or transactional semantics differ.
