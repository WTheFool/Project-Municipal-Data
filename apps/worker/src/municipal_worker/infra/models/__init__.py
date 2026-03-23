from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from .run import Run  # noqa: E402
from .artifact import RunArtifact  # noqa: E402
