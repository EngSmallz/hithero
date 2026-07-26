# Database migrations

This directory is the versioned schema-change boundary for production. The
current baseline revision is intentionally empty until the production SQL
production SQL Server schema is captured and reviewed. Do not run `Base.metadata.create_all`
against production.

Before applying the baseline in a deployment:

1. Take and verify a database backup.
2. Export the production schema and compare table/column/index/constraint
   names with `backend/db/models.py`.
3. Stamp the existing database at `20260711_0001_baseline` only after that
   comparison is reviewed.
4. Rehearse upgrades and rollback/restore against a production-shaped copy.

Future revisions must be additive or include an explicit data/backout plan.
