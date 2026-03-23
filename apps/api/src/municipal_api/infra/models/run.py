import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, Text
from municipal_api.infra.db import Base

def _uuid() -> str:
    return str(uuid.uuid4())

class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="runs")
    artifacts: Mapped[list["RunArtifact"]] = relationship(back_populates="run")
