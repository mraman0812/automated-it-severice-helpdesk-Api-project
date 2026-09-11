from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict


class TrainingRunResponse(BaseModel):
    id: int
    model_id: Optional[int] = None
    dataset_version: str
    training_samples: int
    test_samples: int
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    training_duration_seconds: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    logs: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ModelResponse(BaseModel):
    id: int
    model_name: str
    model_type: str
    version: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    file_path: str
    status: str
    trained_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrainRequest(BaseModel):
    model_name: Optional[str] = "TicketClassifier"
    version: Optional[str] = None
    algorithm: Optional[str] = "LogisticRegression"  # or "LinearSVC"


class TrainResponse(BaseModel):
    message: str
    model_id: int
    run_id: int
    version: str
    status: str
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None


class ModelEvaluationResponse(BaseModel):
    model_id: int
    version: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    categories: List[str]
    classification_report: Dict[str, Dict[str, float]]
