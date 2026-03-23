import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime
from municipal_api.infra.db import Base

def _uuid() -> str:
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    uploads: Mapped[list["Upload"]] = relationship(back_populates="project")
    runs: Mapped[list["Run"]] = relationship(back_populates="project")
