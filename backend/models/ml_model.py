from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    BigInteger
)

from database import Base



class MLModel(Base):
    __tablename__ = "ml_models"

    artifact_path = Column(String(500), nullable=True)
    artifact_filename = Column(String(255), nullable=True)
    artifact_size_bytes = Column(BigInteger, nullable=True)
    artifact_sha256 = Column(String(64), nullable=True)

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False,
        index=True
    )

    version = Column(
        String(50),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    framework = Column(
        String(50),
        nullable=True
    )

    status = Column(
        String(30),
        default="registered",
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

