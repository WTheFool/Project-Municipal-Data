import uuid
from datetime import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from sqlalchemy.orm import Session

from municipal_api.infra.db import get_db
from municipal_api.infra.models import Project, Upload, Run
from municipal_api.infra.queue_rq import get_queue
from municipal_api.infra.settings import settings
from municipal_api.infra.storage_s3 import ensure_bucket_exists, s3_client

router = APIRouter()

def _storage_key(project_id: str, upload_id: str, filename: str) -> str:
    safe = filename.replace("\\", "_").replace("/", "_")
    return f"projects/{project_id}/uploads/{upload_id}/{safe}"

@router.post("/projects/{project_id}/uploads")
async def upload_files_to_project(
    project_id: str,
    files: list[UploadFile],
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    ensure_bucket_exists()
    s3 = s3_client()

    created: list[dict] = []
    for f in files:
        upload = Upload(project_id=project_id, filename=f.filename or "upload.xlsx", storage_key="pending")
        db.add(upload)
        db.commit()
        db.refresh(upload)

        key = _storage_key(project_id, upload.id, upload.filename)
        content = await f.read()
        s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=content)

        upload.storage_key = key
        db.commit()
        created.append({"upload_id": upload.id, "filename": upload.filename, "storage_key": key})

    return {"project_id": project_id, "uploads": created}

@router.post("/upload")
async def upload_and_start_run(
    files: list[UploadFile],
    years: str | None = Form(None),
    graph_mode: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """
    Convenience endpoint used by the current web UI:
    - creates a new project
    - stores uploaded files
    - creates a run
    - enqueues the worker job
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    project = Project(name=f"Upload {datetime.utcnow().isoformat(timespec='seconds')} ({uuid.uuid4().hex[:6]})")
    db.add(project)
    db.commit()
    db.refresh(project)

    uploads_resp = await upload_files_to_project(project.id, files, db)
    upload_ids = [u["upload_id"] for u in uploads_resp["uploads"]]

    run = Run(project_id=project.id, status="queued")
    db.add(run)
    db.commit()
    db.refresh(run)

    storage_keys = [u["storage_key"] for u in uploads_resp["uploads"]]

    years_list: list[int] | None = None
    if years:
        try:
            parsed = json.loads(years)
            if isinstance(parsed, list):
                years_list = [int(x) if x is not None else None for x in parsed]
        except Exception:
            years_list = None

    q = get_queue()
    mode = (graph_mode or "municipal").strip().lower()
    if mode not in ("municipal", "askew"):
        mode = "municipal"
    job = q.enqueue(
        "municipal_worker.jobs.standardize_run.standardize_run",
        run.id,
        project.id,
        storage_keys,
        years_list,
        mode,
    )

    return {"project_id": project.id, "upload_ids": upload_ids, "run_id": run.id, "job_id": job.id}