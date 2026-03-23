from fastapi import APIRouter, HTTPException
from rq.job import Job

from municipal_api.infra.queue_rq import redis_conn

router = APIRouter()

@router.get("/job/{job_id}")
def get_job_status(job_id: str):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.get_id(),
        "status": job.get_status(),
        "progress": job.meta.get("progress", 0),
        "result": job.result if job.is_finished else None
    }