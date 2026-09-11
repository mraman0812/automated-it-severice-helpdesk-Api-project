from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.exceptions import UnauthorizedException, ConflictException, NotFoundException
from app.database.database import get_db
from app.models.user import User
from app.models.role import Role, RoleEnum
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.schemas.user import UserResponse
from app.api.deps import get_current_user
from app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise ConflictException("An account with this email address already exists", error_code="EMAIL_EXISTS")

    employee_role = db.query(Role).filter(Role.name == RoleEnum.EMPLOYEE.value).first()
    if not employee_role:
        employee_role = Role(name=RoleEnum.EMPLOYEE.value, description="General Employee")
        db.add(employee_role)
        db.flush()

    hashed_pw = get_password_hash(user_in.password)
    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hashed_pw,
        role_id=employee_role.id,
        department_id=user_in.department_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    AuditService.log_action(
        db=db,
        action="USER_REGISTERED",
        entity_type="user",
        entity_id=str(user.id),
        user_id=user.id,
    )
    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: Session = Depends(get_db),
):
    # Support both JSON payload and Form Data (Swagger UI OAuth2 Password flow)
    content_type = request.headers.get("content-type", "")
    email = None
    password = None

    if "application/json" in content_type:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
    else:
        form = await request.form()
        email = form.get("username") or form.get("email")
        password = form.get("password")

    if not email or not password:
        raise UnauthorizedException("Email and password are required", error_code="INVALID_CREDENTIALS")

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedException("Incorrect email or password", error_code="INVALID_CREDENTIALS")

    if not user.is_active:
        raise UnauthorizedException("User account is inactive", error_code="ACCOUNT_INACTIVE")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(user.id, expires_delta=access_token_expires)

    AuditService.log_action(
        db=db,
        action="USER_LOGIN",
        entity_type="user",
        entity_id=str(user.id),
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.name if user.role else "EMPLOYEE",
            "department": user.department.name if user.department else None,
        },
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
