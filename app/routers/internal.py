"""Internal endpoints that a cron service calls to trigger the scheduled jobs."""
import threading
from fastapi import APIRouter, Depends, Request

from app.dependencies import verify_cronjob_request
from app.services.jobs import wednesday_job, tuesday_job, thursday_job, daily_job

router = APIRouter()

@router.post("/internal/run-wednesday-job")
async def run_wednesday_job(request: Request, _: None = Depends(verify_cronjob_request)):
    threading.Thread(target=wednesday_job, daemon=True).start()
    return {"status": "wednesday job started"}

@router.post("/internal/run-tuesday-job")
async def run_tuesday_job(request: Request, _: None = Depends(verify_cronjob_request)):
    threading.Thread(target=tuesday_job, daemon=True).start()
    return {"status": "tuesday job started"}

@router.post("/internal/run-thursday-job")
async def run_thursday_job(request: Request, _: None = Depends(verify_cronjob_request)):
    threading.Thread(target=thursday_job, daemon=True).start()
    return {"status": "thursday job started"}

@router.post("/internal/run-daily-job")
async def run_daily_job(request: Request, _: None = Depends(verify_cronjob_request)):
    threading.Thread(target=daily_job, daemon=True).start()
    return {"status": "daily job started"}