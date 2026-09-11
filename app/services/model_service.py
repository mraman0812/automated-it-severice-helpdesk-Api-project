import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import NotFoundException
from app.models.ml_model import MLModel, ModelTrainingRun, ModelStatusEnum, TrainingRunStatusEnum
from app.ml.train import train_models
from app.ml.model_manager import model_manager


class ModelService:
    @staticmethod
    def list_models(db: Session) -> List[MLModel]:
        return db.query(MLModel).order_by(MLModel.id.desc()).all()

    @staticmethod
    def get_model(db: Session, model_id: int) -> MLModel:
        model = db.query(MLModel).filter(MLModel.id == model_id).first()
        if not model:
            raise NotFoundException(f"ML Model #{model_id} not found", error_code="MODEL_NOT_FOUND")
        return model

    @classmethod
    def train_and_register_model(
        cls,
        db: Session,
        model_name: str = "TicketClassifier",
        version: Optional[str] = None,
        algorithm: str = "LogisticRegression",
    ) -> Dict[str, Any]:
        if not version:
            count = db.query(MLModel).count()
            version = f"v{count + 1}.0"

        started_at = datetime.now(timezone.utc)
        training_run = ModelTrainingRun(
            dataset_version="v1.0",
            status=TrainingRunStatusEnum.RUNNING,
            started_at=started_at,
        )
        db.add(training_run)
        db.commit()
        db.refresh(training_run)

        try:
            metadata = train_models(version=version, algorithm=algorithm)

            model_record = MLModel(
                model_name=model_name,
                model_type=f"TFIDF_{algorithm}",
                version=version,
                accuracy=metadata["overall_accuracy"],
                precision=metadata["category_metrics"]["precision"],
                recall=metadata["category_metrics"]["recall"],
                f1_score=metadata["overall_f1"],
                file_path=settings.MODEL_DIR,
                status=ModelStatusEnum.ACTIVE,
                trained_at=datetime.now(timezone.utc),
            )

            # Set previous active models to INACTIVE
            db.query(MLModel).filter(MLModel.status == ModelStatusEnum.ACTIVE).update(
                {"status": ModelStatusEnum.INACTIVE}
            )

            db.add(model_record)
            db.flush()

            training_run.model_id = model_record.id
            training_run.training_samples = metadata["training_samples"]
            training_run.test_samples = metadata["test_samples"]
            training_run.accuracy = metadata["overall_accuracy"]
            training_run.precision = metadata["category_metrics"]["precision"]
            training_run.recall = metadata["category_metrics"]["recall"]
            training_run.f1_score = metadata["overall_f1"]
            training_run.training_duration_seconds = metadata["duration_seconds"]
            training_run.completed_at = datetime.now(timezone.utc)
            training_run.status = TrainingRunStatusEnum.COMPLETED
            training_run.logs = f"Successfully trained {algorithm} with accuracy {metadata['overall_accuracy']:.4f}"

            db.commit()
            db.refresh(model_record)

            # Reload in-memory cache
            model_manager.load_models()

            return {
                "message": "Model trained and activated successfully",
                "model_id": model_record.id,
                "run_id": training_run.id,
                "version": version,
                "status": "ACTIVE",
                "accuracy": model_record.accuracy,
                "f1_score": model_record.f1_score,
            }

        except Exception as e:
            logger.error("Training run failed: %s", e)
            training_run.status = TrainingRunStatusEnum.FAILED
            training_run.completed_at = datetime.now(timezone.utc)
            training_run.logs = str(e)
            db.commit()
            raise

    @staticmethod
    def activate_model(db: Session, model_id: int) -> MLModel:
        target_model = db.query(MLModel).filter(MLModel.id == model_id).first()
        if not target_model:
            raise NotFoundException("Model not found", error_code="MODEL_NOT_FOUND")

        db.query(MLModel).filter(MLModel.status == ModelStatusEnum.ACTIVE).update(
            {"status": ModelStatusEnum.INACTIVE}
        )
        target_model.status = ModelStatusEnum.ACTIVE
        db.commit()
        db.refresh(target_model)

        model_manager.load_models()
        return target_model
