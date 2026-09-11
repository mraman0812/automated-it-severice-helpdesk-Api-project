from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException
from app.database.database import get_db
from app.models.user import User
from app.models.role import Role, RoleEnum
from app.schemas.user import UserResponse, UserUpdate
from app.api.deps import get_current_user, require_roles
from app.services.audit_service import AuditService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = None,
    department_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.AGENT])),
):
    query = db.query(User)
    if role:
        query = query.join(Role).filter(Role.name == role)
    if department_id:
        query = query.filter(User.department_id == department_id)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.all()


@router.get("/agents", response_model=List[UserResponse])
def list_agents(
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent_role = db.query(Role).filter(Role.name == RoleEnum.AGENT.value).first()
    if not agent_role:
        return []
    query = db.query(User).filter(User.role_id == agent_role.id, User.is_active == True)  # noqa: E712
    if department_id:
        query = query.filter(User.department_id == department_id)
    return query.all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Users can view their own profile, managers/admins can view any
    role_name = current_user.role.name if current_user.role else RoleEnum.EMPLOYEE.value
    if current_user.id != user_id and role_name not in [RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]:
        raise ForbiddenException("Permission denied to view this user")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User not found", error_code="USER_NOT_FOUND")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.MANAGER, RoleEnum.ADMIN])),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User not found", error_code="USER_NOT_FOUND")

    # Only admin can change roles
    curr_role = current_user.role.name if current_user.role else ""
    if user_update.role_id is not None and curr_role != RoleEnum.ADMIN.value:
        raise ForbiddenException("Only administrators can modify user roles")

    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))

    for field, val in update_data.items():
        setattr(user, field, val)

    AuditService.log_action(
        db=db,
        action="USER_UPDATED",
        entity_type="user",
        entity_id=str(user.id),
        user_id=current_user.id,
        details={"updated_fields": list(update_data.keys())},
    )

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.ADMIN])),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User not found", error_code="USER_NOT_FOUND")

    db.delete(user)
    db.commit()
    return None
