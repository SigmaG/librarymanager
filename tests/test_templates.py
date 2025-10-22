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
from librarymanager.models import Book


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
def test_new_item_pages_render(app):
    client = app.test_client()
    paths = ['/items/new', '/items/new/book', '/items/new/cd', '/items/new/dvd', '/items/new/boardgame']
    for p in paths:
        r = client.get(p)
        assert r.status_code == 200, f"{p} returned {r.status_code}\n{r.get_data(as_text=True)[:200]}"


def test_type_list_pages_render(app):
    client = app.test_client()
    # create one item of each type and ensure it appears on the corresponding listing page
    with app.app_context():
        from librarymanager.models import Book, CD, DVD, BoardGame
        b = Book(title='Book A', language='en')
        c = CD(title='CD A', primary_artist='Artist')
        d = DVD(title='DVD A')
        g = BoardGame(title='Game A')
        db.session.add_all([b, c, d, g])
        db.session.commit()

    mapping = {
        '/items/type/book': 'Book A',
        '/items/type/cd': 'CD A',
        '/items/type/dvd': 'DVD A',
        '/items/type/boardgame': 'Game A',
    }

    for p, title in mapping.items():
        # follow Next links using cursor until found or no next
    
        found = False
        resp = client.get(p)
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        if title in body:
            found = True
        else:
            import re
            while True:
                m = re.search(r'href="([^"]*cursor=([A-Za-z0-9_\-]+)[^"]*)"', body)
                if not m:
                    break
                next_url = m.group(1)
                resp = client.get(next_url)
                assert resp.status_code == 200
                body = resp.get_data(as_text=True)
                if title in body:
                    found = True
                    break
        assert found, f"{title} not found in any page of {p}"


def test_item_detail_renders(app):
    # create a book so we have a detail page
    with app.app_context():
        b = Book(title='Template Test Book', language='en')
        db.session.add(b)
        db.session.commit()
        bid = b.id

    client = app.test_client()
    r = client.get(f'/items/{bid}')
    assert r.status_code == 200
