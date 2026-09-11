from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.classification import (
    PredictRequest,
    PredictResponse,
    BatchPredictRequest,
    BatchPredictResponse,
)
from app.services.classification_service import ClassificationService

router = APIRouter(prefix="/classification", tags=["Classification"])


@router.post("/predict", response_model=PredictResponse)
def predict_ticket(request: PredictRequest, db: Session = Depends(get_db)):
    """
    Standalone endpoint to test ML prediction independently without creating a ticket.
    """
    prediction = ClassificationService.predict_ticket(
        title=request.title,
        description=request.description,
        db=db,
    )
    return PredictResponse(
        category=prediction["category"],
        subcategory=prediction["subcategory"],
        priority=prediction["priority"],
        department=prediction["department"],
        confidence=prediction["confidence"],
        needs_review=prediction["needs_review"],
    )


@router.post("/batch", response_model=BatchPredictResponse)
def batch_predict(request: BatchPredictRequest, db: Session = Depends(get_db)):
    """
    Batch classification endpoint for high-throughput automated classification.
    """
    results = []
    for item in request.tickets:
        pred = ClassificationService.predict_ticket(
            title=item.title,
            description=item.description,
            db=db,
        )
        results.append(PredictResponse(
            category=pred["category"],
            subcategory=pred["subcategory"],
            priority=pred["priority"],
            department=pred["department"],
            confidence=pred["confidence"],
            needs_review=pred["needs_review"],
        ))
    return BatchPredictResponse(results=results)
