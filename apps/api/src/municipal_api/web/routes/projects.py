from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from municipal_api.infra.db import get_db
from municipal_api.infra.models import Project, Upload, Run

router = APIRouter()

@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    items = db.query(Project).order_by(Project.created_at.desc()).all()
    return [{"id": p.id, "name": p.name, "created_at": p.created_at.isoformat()} for p in items]

@router.get("/projects/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    uploads = db.query(Upload).filter(Upload.project_id == project_id).order_by(Upload.created_at.desc()).all()
    runs = db.query(Run).filter(Run.project_id == project_id).order_by(Run.created_at.desc()).all()
    return {
        "id": p.id,
        "name": p.name,
        "created_at": p.created_at.isoformat(),
        "uploads": [{"id": u.id, "filename": u.filename, "created_at": u.created_at.isoformat()} for u in uploads],
        "runs": [{"id": r.id, "status": r.status, "created_at": r.created_at.isoformat()} for r in runs],
    }

@router.post("/projects")
def create_project(name: str, db: Session = Depends(get_db)):
    p = Project(name=name)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name, "created_at": p.created_at.isoformat()}
