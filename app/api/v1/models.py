from typing import List
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.role import RoleEnum
from app.models.ml_model import MLModel, ModelTrainingRun
from app.schemas.ml_model import (
    ModelResponse,
    TrainRequest,
    TrainResponse,
    TrainingRunResponse,
)
from app.api.deps import require_roles
from app.services.model_service import ModelService

router = APIRouter(prefix="/models", tags=["Model Management"])


@router.get("", response_model=List[ModelResponse])
def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.MANAGER])),
):
    return ModelService.list_models(db)


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.MANAGER])),
):
    return ModelService.get_model(db, model_id)


@router.post("/train", response_model=TrainResponse, status_code=status.HTTP_200_OK)
def trigger_training(
    train_in: TrainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.ADMIN])),
):
    result = ModelService.train_and_register_model(
        db=db,
        model_name=train_in.model_name or "TicketClassifier",
        version=train_in.version,
        algorithm=train_in.algorithm or "LogisticRegression",
    )
    return result


@router.post("/{model_id}/activate", response_model=ModelResponse)
def activate_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.ADMIN])),
):
    return ModelService.activate_model(db, model_id)


@router.get("/training-runs/history", response_model=List[TrainingRunResponse])
def list_training_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.MANAGER])),
):
    return db.query(ModelTrainingRun).order_by(ModelTrainingRun.id.desc()).limit(50).all()
