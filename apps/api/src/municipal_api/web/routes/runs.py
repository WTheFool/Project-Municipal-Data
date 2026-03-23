from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from municipal_api.infra.db import get_db
from municipal_api.infra.models import Project, Upload, Run, RunArtifact
from municipal_api.infra.queue_rq import get_queue

router = APIRouter()

@router.post("/projects/{project_id}/runs")
def create_run(project_id: str, upload_ids: list[str], db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    uploads = db.query(Upload).filter(Upload.project_id == project_id, Upload.id.in_(upload_ids)).all()
    if len(uploads) != len(upload_ids):
        raise HTTPException(status_code=400, detail="One or more upload_ids not found in project")

    run = Run(project_id=project_id, status="queued")
    db.add(run)
    db.commit()
    db.refresh(run)

    storage_keys = [u.storage_key for u in uploads]
    q = get_queue()
    job = q.enqueue("municipal_worker.jobs.standardize_run.standardize_run", run.id, project_id, storage_keys)

    return {"run_id": run.id, "job_id": job.id, "status": run.status}

@router.get("/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    artifacts = db.query(RunArtifact).filter(RunArtifact.run_id == run_id).all()
    return {
        "id": run.id,
        "project_id": run.project_id,
        "status": run.status,
        "error": run.error,
        "created_at": run.created_at.isoformat(),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "artifacts": [{"kind": a.kind, "storage_key": a.storage_key, "created_at": a.created_at.isoformat()} for a in artifacts],
    }
