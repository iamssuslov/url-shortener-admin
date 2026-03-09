import os
import threading

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session

from app.main import create_app
from app import db as db_module
from app.models import ApiKey
from app.rate_limit import clear_rate_limits
from tests.utils.live_server import run_server, wait_for_server

TEST_DB_FILE = "./test.db"
BASE_URL = "http://127.0.0.1:8005"

pytest_plugins = [
    "tests.ui.fixtures.browser_fixtures",
    "tests.ui.fixtures.hooks",
]


@pytest.fixture(scope="session")
def faker():
    return Faker()


@pytest.fixture
def engine():
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

    eng = create_engine(
        f"sqlite:///{TEST_DB_FILE}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(eng)

    with Session(eng) as session:
        session.add(ApiKey(key="test-api-key", name="tests", is_active=True))
        session.add(ApiKey(key="inactive-api-key", name="inactive", is_active=False))
        session.commit()

    return eng


@pytest.fixture
def app(engine):
    clear_rate_limits()
    db_module.engine = engine
    test_app = create_app()
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def api_headers():
    return {"X-API-Key": "test-api-key"}


@pytest.fixture
def inactive_api_headers():
    return {"X-API-Key": "inactive-api-key"}


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture(scope="session", autouse=True)
def live_server():
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    wait_for_server(BASE_URL)
    yield