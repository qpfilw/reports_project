from __future__ import annotations
import os
import shutil
import sys
import tempfile
from app.core.config import get_settings
from collections.abc import Generator, Iterator
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("PROCESSING_DISPATCH_MODE", "sync")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("CELERY_TASK_EAGER_PROPAGATES", "true")

from app.api.deps import get_db  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.seed import create_admin_user, seed_roles  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import RoleCodeEnum  # noqa: E402

get_settings.cache_clear()
settings = get_settings()

TEST_DATABASE_URL = settings.test_database_url
if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is not set in settings. "
        "Add TEST_DATABASE_URL to backend/.env."
    )

test_storage_dir = Path(tempfile.mkdtemp(prefix="reporting_test_storage_"))
settings.storage_root = str(test_storage_dir)
settings.processing_dispatch_mode = "sync"
settings.celery_task_always_eager = True
settings.celery_task_eager_propagates = True

test_engine = create_engine(
    TEST_DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

@pytest.fixture()
def admin_credentials() -> dict[str, str]:
    return {
        "email": "admin@example.com",
        "password": "Admin12345!",
    }

@pytest.fixture()
def admin_token(client, admin_credentials: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json=admin_credentials,
    )
    assert response.status_code == 200, response.text
    return response.json()["tokens"]["access_token"]

@pytest.fixture()
def admin_auth_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture(scope="session", autouse=True)
def prepare_test_environment() -> Iterator[None]:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    shutil.rmtree(test_storage_dir, ignore_errors=True)


@pytest.fixture(autouse=True)
def reset_database() -> Iterator[None]:
    shutil.rmtree(settings.storage_root_path, ignore_errors=True)
    settings.storage_root_path.mkdir(parents=True, exist_ok=True)

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        seed_roles(db)
        create_admin_user(
            db,
            email="admin@example.com",
            password="Admin12345!",
            full_name="Test Admin",
            position="Administrator",
            department="IT",
        )
        yield
    finally:
        db.close()


@pytest.fixture()
def db_session() -> Iterator[Session]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client