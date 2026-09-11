from typing import List, Optional
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5, max_length=5000)


class PredictResponse(BaseModel):
    category: str
    subcategory: Optional[str] = None
    priority: str
    department: str
    confidence: float
    needs_review: bool


class BatchPredictRequest(BaseModel):
    tickets: List[PredictRequest]


class BatchPredictResponse(BaseModel):
    results: List[PredictResponse]
