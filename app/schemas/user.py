from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DepartmentBrief(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    name: str
    email: EmailStr
    department_id: Optional[int] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str
    role_id: int


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department_id: Optional[int] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role: RoleResponse
    department: Optional[DepartmentBrief] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
