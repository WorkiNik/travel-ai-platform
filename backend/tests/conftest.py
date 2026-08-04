import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Значения по умолчанию для тестового окружения — реальный OPENAI_API_KEY не нужен,
# так как эти тесты не дёргают настоящий AI-сервис
os.environ.setdefault(
    "DATABASE_URL", "postgresql://dev:dev123@localhost:5432/travel_ai_test"
)
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app.db.database import Base, get_db  # noqa: E402
from app import models  # noqa: E402,F401 — регистрирует все модели перед create_all
from app.main import app  # noqa: E402

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Создаёт чистую схему БД один раз на всю тестовую сессию."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
        session.rollback()  # откатываем изменения теста, чтобы тесты не влияли друг на друга
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()