import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.base import Base
from app.database.database import get_db
from app.core.security import get_password_hash, create_access_token
from app.models.role import Role, RoleEnum
from app.models.department import Department
from app.models.category import Category, SubCategory
from app.models.user import User

# In-memory test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed baseline roles
    roles = [
        Role(name=RoleEnum.ADMIN.value, description="Admin"),
        Role(name=RoleEnum.MANAGER.value, description="Manager"),
        Role(name=RoleEnum.AGENT.value, description="Agent"),
        Role(name=RoleEnum.EMPLOYEE.value, description="Employee"),
    ]
    db.add_all(roles)
    db.flush()

    # Seed departments
    dept1 = Department(name="Network Support", description="Network Dept")
    dept2 = Department(name="IT Helpdesk", description="Helpdesk Dept")
    db.add_all([dept1, dept2])
    db.flush()

    # Seed categories
    cat1 = Category(name="Network", description="Network")
    cat2 = Category(name="Account & Access", description="Account")
    db.add_all([cat1, cat2])
    db.flush()

    sub1 = SubCategory(category_id=cat1.id, name="VPN", description="VPN")
    sub2 = SubCategory(category_id=cat2.id, name="Password Reset", description="Password")
    db.add_all([sub1, sub2])
    db.flush()

    # Seed users
    admin_user = User(
        name="Test Admin",
        email="testadmin@example.com",
        password_hash=get_password_hash("TestPass123!"),
        role_id=1,
        is_active=True,
    )
    agent_user = User(
        name="Test Agent",
        email="testagent@example.com",
        password_hash=get_password_hash("TestPass123!"),
        role_id=3,
        department_id=dept1.id,
        is_active=True,
    )
    employee_user = User(
        name="Test Employee",
        email="testemployee@example.com",
        password_hash=get_password_hash("TestPass123!"),
        role_id=4,
        is_active=True,
    )
    db.add_all([admin_user, agent_user, employee_user])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def employee_token(db):
    user = db.query(User).filter(User.email == "testemployee@example.com").first()
    return create_access_token(user.id)


@pytest.fixture
def agent_token(db):
    user = db.query(User).filter(User.email == "testagent@example.com").first()
    return create_access_token(user.id)


@pytest.fixture
def admin_token(db):
    user = db.query(User).filter(User.email == "testadmin@example.com").first()
    return create_access_token(user.id)
