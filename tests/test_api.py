import sys
from pathlib import Path
import tempfile
import pytest

# make src importable
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


def test_create_and_list_items(app):
    client = app.test_client()

    # create a book (language required)
    book_payload = {
        'type': 'book',
        'title': 'API Book',
        'language': 'en',
        'authors': ['Author One', 'Author Two'],
        'genres': ['Fiction']
    }
    r = client.post('/api/items', json=book_payload)
    assert r.status_code == 201
    data = r.get_json()
    assert data['type'] == 'book'
    assert 'Author One' in data['authors']

    # create a cd
    cd_payload = {
        'type': 'cd',
        'title': 'Album X',
        'artist': 'Artist X',
        'genres': ['Rock']
    }
    r = client.post('/api/items', json=cd_payload)
    assert r.status_code == 201

    # create a dvd
    dvd_payload = {
        'type': 'dvd',
        'title': 'Movie Y',
    }
    r = client.post('/api/items', json=dvd_payload)
    assert r.status_code == 201

    # create a board game using alias
    bg_payload = {
        'type': 'boardgame',
        'title': 'Fun Game',
        'min_players': 2,
        'max_players': 6,
        'authors': ['Designer A'],
        'genres': ['Strategy']
    }
    r = client.post('/api/items', json=bg_payload)
    assert r.status_code == 201

    # list items
    r = client.get('/api/items')
    assert r.status_code == 200
    items = r.get_json()
    titles = {it['title'] for it in items}
    assert 'API Book' in titles
    assert 'Album X' in titles
    assert 'Movie Y' in titles
    assert 'Fun Game' in titles
