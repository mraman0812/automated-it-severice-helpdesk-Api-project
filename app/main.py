import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import HelpdeskException
from app.database.database import init_db
from app.ml.model_manager import model_manager
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("==================================================")
    logger.info(" Starting Automated IT Helpdesk System           ")
    logger.info("==================================================")
    
    # 1. Initialize database tables
    try:
        init_db()
        logger.info("✓ Database initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # 2. Pre-load ML models into memory
    loaded = model_manager.load_models()
    if loaded:
        logger.info("✓ ML Models loaded into memory cache.")
    else:
        logger.warning("! ML Models not loaded yet. Train models using scripts/train_model.py or /api/v1/models/train.")

    # 3. Ensure uploads directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    yield

    logger.info("Shutting down Automated IT Helpdesk System...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Automated IT Support Ticket Classification, Lifecycle Management, and Predictive Analytics API.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers per PRD section 55 & 90
@app.exception_handler(HelpdeskException)
async def helpdesk_exception_handler(request: Request, exc: HelpdeskException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
            "data": exc.data,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = ".".join(str(l) for l in err["loc"] if l != "body")
        errors.append(f"{loc}: {err['msg']}" if loc else err["msg"])
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "; ".join(errors) if errors else "Validation failed",
            "error_code": "VALIDATION_ERROR",
            "data": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred",
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )


# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount Static Files and Dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def root_redirect():
    # If static dashboard exists, serve it, otherwise redirect to docs
    dashboard_index = os.path.join(static_dir, "index.html")
    if os.path.exists(dashboard_index):
        return FileResponse(dashboard_index)
    return FileResponse(dashboard_index)


@app.get("/dashboard", include_in_schema=False)
def get_dashboard():
    dashboard_index = os.path.join(static_dir, "index.html")
    return FileResponse(dashboard_index)


@app.get("/health", tags=["Health"], include_in_schema=True)
def root_health():
    from app.api.v1.health import health_check
    from app.database.database import SessionLocal
    db = SessionLocal()
    try:
        return health_check(db=db)
    finally:
        db.close()
