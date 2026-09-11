from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.role import RoleEnum
from app.models.department import Department
from app.models.category import Category, SubCategory
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    CategoryCreate,
    CategoryResponse,
    SubCategoryCreate,
    SubCategoryResponse,
)
from app.api.deps import get_current_user, require_roles
from app.core.exceptions import NotFoundException, ConflictException

router = APIRouter(tags=["Departments & Categories"])


@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(db: Session = Depends(get_db)):
    return db.query(Department).filter(Department.is_active == True).all()  # noqa: E712


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.ADMIN])),
):
    existing = db.query(Department).filter(Department.name == dept_in.name).first()
    if existing:
        raise ConflictException("Department with this name already exists")
    dept = Department(name=dept_in.name, description=dept_in.description, email=dept_in.email)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).filter(Category.is_active == True).all()  # noqa: E712


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    cat_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.ADMIN])),
):
    existing = db.query(Category).filter(Category.name == cat_in.name).first()
    if existing:
        raise ConflictException("Category already exists")
    cat = Category(name=cat_in.name, description=cat_in.description)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.post("/categories/{category_id}/subcategories", response_model=SubCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_subcategory(
    category_id: int,
    sub_in: SubCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.ADMIN])),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise NotFoundException("Parent category not found")
    sub = SubCategory(category_id=cat.id, name=sub_in.name, description=sub_in.description)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub
