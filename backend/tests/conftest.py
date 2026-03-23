from __future__ import annotations
import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterator
import pytest
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

TEST_ROOT = Path(tempfile.mkdtemp(prefix="erp_backend_tests_"))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{(TEST_ROOT / 'test.db').as_posix()}")
os.environ.setdefault("STORAGE_ROOT", str(TEST_ROOT / "storage"))
os.environ.setdefault("PROCESSING_DISPATCH_MODE", "sync")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("CELERY_TASK_EAGER_PROPAGATES", "true")

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

import app.db.session as db_session_module  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.seed import create_admin_user, seed_roles  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402

test_engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
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

db_session_module.engine = test_engine
db_session_module.SessionLocal = TestingSessionLocal

@pytest.fixture(autouse=True)
def reset_database() -> Iterator[None]:
    settings = get_settings()
    shutil.rmtree(settings.storage_root_path, ignore_errors=True)
    settings.storage_root_path.mkdir(parents=True, exist_ok=True)

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    with TestingSessionLocal() as db:
        seed_roles(db)
        create_admin_user(
            db,
            email="admin@example.com",
            password="AdminPass123!",
            full_name="System Administrator",
            position="Administrator",
            department="IT",
        )
    yield


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture()
def db_session() -> Iterator[Session]:
    with TestingSessionLocal() as session:
        yield session

@pytest.fixture()
def admin_user(db_session: Session) -> User:
    user = db_session.query(User).filter(User.email == "admin@example.com").one()
    return user

@pytest.fixture()
def admin_credentials() -> dict[str, str]:
    return {"email": "admin@example.com", "password": "AdminPass123!"}
