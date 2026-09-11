from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.database import get_db
from app.ml.model_manager import model_manager

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    db_status = "unhealthy"
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unreachable"

    predictor = model_manager.get_predictor()
    model_ready = predictor.is_ready

    return {
        "status": "healthy" if db_status == "healthy" and model_ready else "degraded",
        "database": db_status,
        "ml_model": "loaded" if model_ready else "heuristic_fallback",
        "services": {
            "database": db_status,
            "category_model": "healthy" if predictor.category_model else "not_loaded",
            "priority_model": "healthy" if predictor.priority_model else "not_loaded",
            "subcategory_model": "healthy" if predictor.subcategory_model else "not_loaded",
        },
    }
