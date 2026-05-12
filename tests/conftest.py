import pytest
import data.db as db_module
from data.db import init_db


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test_sessions.db"
    monkeypatch.setattr(db_module, "DB_PATH", db_file)
    init_db()
    yield db_file
