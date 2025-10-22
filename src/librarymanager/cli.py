import hashlib
import os
from pathlib import Path

import click
from flask import current_app


def _models_hash(models_path: Path) -> str:
    h = hashlib.sha256()
    h.update(models_path.read_bytes())
    return h.hexdigest()


def init_app(app):
    @app.cli.command('recreate-db')
    @click.option('--force', is_flag=True, help='Always destroy and recreate the database')
    @click.option('--seed', is_flag=True, help='Seed the database with example data')
    def recreate_db(force: bool, seed: bool):
        """Destroy and recreate the SQLite database when models change.

        The command computes a hash of `src/librarymanager/models.py` and
        compares it with the stored hash in `instance/.models_hash`. If the
        hash differs (models changed) or `--force` is used, the DB file is
        removed and the schema recreated with `db.create_all()`.
        """
        from .extensions import db

        app = current_app._get_current_object()

        # locate models file
        project_root = Path(app.root_path).parents[1]
        models_path = project_root / 'src' / app.import_name.split('.')[-1] / 'models.py'
        if not models_path.exists():
            click.echo(f'Could not find models file at {models_path}. Aborting.')
            raise SystemExit(1)

        current_hash = _models_hash(models_path)

        instance_dir = Path(app.instance_path)
        instance_dir.mkdir(parents=True, exist_ok=True)
        hash_file = instance_dir / '.models_hash'

        prev_hash = None
        if hash_file.exists():
            prev_hash = hash_file.read_text().strip()

        # determine sqlite file path from SQLALCHEMY_DATABASE_URI when possible
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        sqlite_path = None
        if db_uri.startswith('sqlite:///'):
            sqlite_path = Path(db_uri.replace('sqlite:///', ''))
        else:
            # fallback to instance/library.sqlite3
            sqlite_path = instance_dir / 'library.sqlite3'

        should_recreate = force or (prev_hash != current_hash)

        if not should_recreate:
            click.echo('No model changes detected and --force not provided. Skipping recreation.')
            return

        # destroy DB file if exists
        if sqlite_path.exists():
            click.echo(f'Removing database file: {sqlite_path}')
            try:
                sqlite_path.unlink()
            except Exception as e:
                click.echo(f'Failed to remove DB file: {e}')
                raise

        # recreate schema
        with app.app_context():
            click.echo('Recreating database schema (db.create_all)...')
            db.create_all()

            if seed:
                click.echo('Seeding example data...')
                # lightweight seed: add one of each type (authors/genres)
                from .models import Author, Genre, Book, CD, DVD, BoardGame

                a1 = Author(name='Sample Author')
                g1 = Genre(name='Sample Genre')
                db.session.add_all([a1, g1])
                db.session.flush()

                book = Book(title='Example Book', description='An example', language='en', publisher='ExamplePub', length=123, size='200x130mm')
                book.authors.append(a1)
                book.genres.append(g1)

                cd = CD(title='Example CD', description='Sample CD', primary_artist='Sample Artist', publisher='MusicPub', duration_minutes=42, track_list=['Track 1', 'Track 2'])
                cd.genres.append(g1)

                dvd = DVD(title='Example DVD', description='Sample DVD', director='Jane Doe', main_actors='Actor A, Actor B', genre='Drama', duration_minutes=120)
                dvd.genres.append(g1)

                bg = BoardGame(title='Example Game', description='Sample board game', author_note='Designer', min_players=2, max_players=4, genre='Family')
                bg.genres.append(g1)

                db.session.add_all([book, cd, dvd, bg])
                db.session.commit()

        # save current hash
        hash_file.write_text(current_hash)
        click.echo('Database recreated and model hash updated.')
