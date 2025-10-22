# Library Manager (skeleton)

Minimal Flask + SQLite skeleton (server-rendered + JSON API) using Python 3.12.

Usage (development):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
export FLASK_APP=run.py
flask db init
flask db migrate
flask db upgrade
flask run
```

Run tests:

```bash
pip install -r requirements-dev.txt
pytest -q
```

Files of interest:
- `src/librarymanager` — application package
- `pyproject.toml` — project metadata (Python 3.12)
- `tests/` — pytest tests

Management commands

The app supplies a Flask CLI command `recreate-db` which will remove the SQLite
database when models change and recreate the schema. It also stores a small
hash in `instance/.models_hash` so the DB is only destroyed when `models.py`
actually changes.

Usage:

```bash
export FLASK_APP=run.py
flask recreate-db          # destroys DB if models changed
flask recreate-db --force  # force destroy
flask recreate-db --seed   # recreate and seed sample data
```
