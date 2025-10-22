import sys
from pathlib import Path
import tempfile

# make src importable
ROOT = Path(__file__).resolve().parents[1]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from librarymanager import create_app
from librarymanager.extensions import db
from librarymanager.models import Book


def make_app():
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
    return app


def test_pagination_books():
    app = make_app()
    with app.app_context():
        # create 25 books
        books = [Book(title=f'Book {i}', language='en') for i in range(25)]
        db.session.add_all(books)
        db.session.commit()

    client = app.test_client()
    # search across pages for some sample titles to be robust to seeded data
    def find_on_pages(path, title):
        # follow Next links using cursor until found or no next
        resp = client.get(path)
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        if title in body:
            return True
        import re
        # follow next link if present
        while True:
            m = re.search(r'href="([^"]*cursor=([A-Za-z0-9_\-]+)[^"]*)"', body)
            if not m:
                return False
            next_url = m.group(1)
            resp = client.get(next_url)
            assert resp.status_code == 200
            body = resp.get_data(as_text=True)
            if title in body:
                return True

    assert find_on_pages('/items/type/book', 'Book 0')
    assert find_on_pages('/items/type/book', 'Book 9')
    assert find_on_pages('/items/type/book', 'Book 10')
    assert find_on_pages('/items/type/book', 'Book 20')

    # Test backward pagination: navigate forward to get a cursor, then go back
    resp = client.get('/items/type/book')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    import re
    m = re.search(r'href="([^"]*cursor=([A-Za-z0-9_\-]+)[^"]*)"', body)
    assert m
    next_url = m.group(1)
    # go forward once
    resp2 = client.get(next_url)
    assert resp2.status_code == 200
    body2 = resp2.get_data(as_text=True)
    # capture prev link
    m2 = re.search(r'href="([^"]*direction=prev[^"]*)"', body2)
    assert m2
    prev_url = m2.group(1)
    resp_prev = client.get(prev_url)
    assert resp_prev.status_code == 200
    # check that we returned to a page containing Book 0 (or similar earlier item)
    assert 'Book 0' in resp_prev.get_data(as_text=True) or 'Book 1' in resp_prev.get_data(as_text=True)


def test_create_and_edit_book_via_forms():
    app = make_app()
    client = app.test_client()

    # create book via form POST
    create_resp = client.post('/items/new/book', data={'title': 'Form Book', 'language': 'en'}, follow_redirects=True)
    assert create_resp.status_code == 200
    body = create_resp.get_data(as_text=True)
    assert 'Form Book' in body

    # find id from redirect by searching for /items/<id> in body
    import re
    m = re.search(r"/items/(\d+)", body)
    assert m, 'detail link not found after create'
    item_id = int(m.group(1))

    # GET edit form and check prefilled title
    edit_get = client.get(f'/items/{item_id}/edit')
    assert edit_get.status_code == 200
    assert 'Form Book' in edit_get.get_data(as_text=True)

    # POST edit to change the title
    edit_post = client.post(f'/items/{item_id}/edit', data={'title': 'Form Book Updated', 'language': 'en'}, follow_redirects=True)
    assert edit_post.status_code == 200
    assert 'Form Book Updated' in edit_post.get_data(as_text=True)
