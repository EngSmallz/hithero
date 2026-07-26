import logging
from dataclasses import dataclass
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JobRun:
    name: str
    started_at: datetime
    completed_at: datetime
    succeeded: bool
    error: str | None = None


def run_one_shot_job(name, job_callable):
    """Run one scheduler invocation to completion and return observable status."""
    started_at = datetime.now(timezone.utc)
    try:
        job_callable()
    except Exception as exc:
        completed_at = datetime.now(timezone.utc)
        logger.exception("Job %s failed", name)
        return JobRun(name, started_at, completed_at, False, str(exc))
    completed_at = datetime.now(timezone.utc)
    logger.info("Job %s completed", name)
    return JobRun(name, started_at, completed_at, True)
