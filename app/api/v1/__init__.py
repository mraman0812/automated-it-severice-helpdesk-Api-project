from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.tickets import router as tickets_router
from app.api.v1.classification import router as classification_router
from app.api.v1.comments import router as comments_router
from app.api.v1.attachments import router as attachments_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.models import router as models_router
from app.api.v1.departments import router as departments_router
from app.api.v1.health import router as health_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(tickets_router)
api_router.include_router(classification_router)
api_router.include_router(comments_router)
api_router.include_router(attachments_router)
api_router.include_router(feedback_router)
api_router.include_router(analytics_router)
api_router.include_router(models_router)
api_router.include_router(departments_router)
api_router.include_router(health_router)

__all__ = ["api_router"]
