from backend.jobs.runner import run_one_shot_job


def test_one_shot_job_runner_reports_success_and_completion():
    calls = []
    result = run_one_shot_job("daily", lambda: calls.append("ran"))

    assert calls == ["ran"]
    assert result.name == "daily"
    assert result.succeeded is True
    assert result.error is None
    assert result.completed_at >= result.started_at


def test_one_shot_job_runner_reports_failure_without_hiding_error():
    result = run_one_shot_job("daily", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    assert result.succeeded is False
    assert result.error == "boom"
