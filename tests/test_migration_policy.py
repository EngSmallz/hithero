from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_production_startup_does_not_use_create_all_implicitly():
    source = (ROOT / "backend/main.py").read_text(encoding="utf-8")

    assert 'if settings.app_env in LOCAL_APP_ENVS:' in source
    assert "Base.metadata.create_all(bind=database_resources.engine)" in source
    assert 'if settings.app_env != "test":' not in source


def test_baseline_migration_and_runbook_are_present():
    baseline = ROOT / "migrations/versions/20260711_0001_baseline.py"
    runbook = ROOT / "migrations/README.md"

    assert baseline.exists()
    assert "intentionally performs no DDL" in baseline.read_text()
    assert "production SQL Server schema" in runbook.read_text()
