import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Integer, String, Float, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class ModelStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class TrainingRunStatusEnum(str, enum.Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MLModel(Base, TimestampMixin):
    __tablename__ = "ml_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "TFIDF_LogisticRegression"
    version: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precision: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    f1_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ModelStatusEnum] = mapped_column(
        Enum(ModelStatusEnum, native_enum=False),
        default=ModelStatusEnum.INACTIVE,
        nullable=False,
    )
    trained_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    training_runs: Mapped[List["ModelTrainingRun"]] = relationship(
        "ModelTrainingRun",
        back_populates="model",
        cascade="all, delete-orphan",
    )


class ModelTrainingRun(Base, TimestampMixin):
    __tablename__ = "model_training_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ml_models.id", ondelete="SET NULL"), nullable=True)
    dataset_version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)

    training_samples: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    test_samples: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precision: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    f1_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    training_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[TrainingRunStatusEnum] = mapped_column(
        Enum(TrainingRunStatusEnum, native_enum=False),
        default=TrainingRunStatusEnum.RUNNING,
        nullable=False,
    )
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    model: Mapped[Optional["MLModel"]] = relationship("MLModel", back_populates="training_runs")
