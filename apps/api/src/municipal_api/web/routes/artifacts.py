import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from municipal_api.infra.db import get_db
from municipal_api.infra.models import RunArtifact
from municipal_api.infra.storage_s3 import s3_client
from municipal_api.infra.settings import settings

router = APIRouter()

@router.get("/runs/{run_id}/artifacts/{kind}")
def get_artifact_json(run_id: str, kind: str, db: Session = Depends(get_db)):
    # MVP: only returns JSON artifacts (profile_json)
    art = db.query(RunArtifact).filter(RunArtifact.run_id == run_id, RunArtifact.kind == kind).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artifact not found")

    s3 = s3_client()
    obj = s3.get_object(Bucket=settings.s3_bucket, Key=art.storage_key)
    data = obj["Body"].read().decode("utf-8")
    return json.loads(data)


@router.get("/runs/{run_id}/artifacts/{kind}/download")
def download_artifact(run_id: str, kind: str, db: Session = Depends(get_db)):
    art = db.query(RunArtifact).filter(RunArtifact.run_id == run_id, RunArtifact.kind == kind).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artifact not found")

    s3 = s3_client()
    obj = s3.get_object(Bucket=settings.s3_bucket, Key=art.storage_key)
    body = obj["Body"]

    filename = art.storage_key.split("/")[-1]
    content_type = obj.get("ContentType") or "application/octet-stream"

    return StreamingResponse(
        body,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
