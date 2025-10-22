import os
import sys
import tempfile
from pathlib import Path

import pytest

# ensure src is importable when running tests from repo root
ROOT = Path(__file__).resolve().parents[1]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from librarymanager import create_app
from librarymanager.extensions import db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.sqlite3')
    cfg = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + db_path,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    }
    app = create_app()
    app.config.update(cfg)

    with app.app_context():
        db.create_all()
        yield app


def test_index(app):
    client = app.test_client()
    resp = client.get('/')
    assert resp.status_code == 200
