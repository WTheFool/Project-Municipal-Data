from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import os

router = APIRouter()

UPLOAD_DIR = Path("uploads")  # Same folder as uploads
EXPORT_DIR = UPLOAD_DIR       # Exports currently go here; adjust if different

@router.get("/download/excel/{filename}")
async def download_excel(filename: str):
    file_path = EXPORT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Excel file not found")
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )

@router.get("/download/word/{filename}")
async def download_word(filename: str):
    file_path = EXPORT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Word file not found")
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename
    )