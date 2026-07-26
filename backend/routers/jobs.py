from fastapi import APIRouter, Depends, Request


def create_jobs_router(*, job_handlers, verify_cronjob_request, run_one_shot_job):
    """Expose the existing authenticated one-shot job triggers."""
    router = APIRouter()

    for job_name in ("wednesday", "tuesday", "thursday", "daily"):
        path = f"/internal/run-{job_name}-job"

        def make_trigger(current_job_name):
            def trigger_job(
                _request: Request,
                _auth: None = Depends(verify_cronjob_request),
            ):
                run_one_shot_job(
                    current_job_name,
                    job_handlers[current_job_name],
                )
                return {"status": f"{current_job_name} job started"}

            return trigger_job

        router.add_api_route(
            path,
            make_trigger(job_name),
            methods=["POST"],
        )

    return router
