from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class SubCategoryResponse(BaseModel):
    id: int
    category_id: int
    name: str
    description: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    subcategories: List[SubCategoryResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SubCategoryCreate(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None


class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    email: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    email: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
