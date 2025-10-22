import sys
from pathlib import Path
import tempfile

import pytest

# ensure src is importable
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


def test_recreate_db_cli(app, monkeypatch):
    runner = app.test_cli_runner()

    # run without force: may recreate on first run or skip if hash exists
    result = runner.invoke(args=['recreate-db'])
    assert ('Recreating database schema' in result.output) or ('No model changes detected' in result.output) or ('Skipping recreation' in result.output)

    # force recreate
    result = runner.invoke(args=['recreate-db', '--force'])
    assert 'Recreating database schema' in result.output

    # recreate with seed
    result = runner.invoke(args=['recreate-db', '--force', '--seed'])
    assert 'Seeding example data' in result.output
