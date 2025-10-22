from .extensions import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)


class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    publication_date = db.Column(db.Date, nullable=True)
    external_id = db.Column(db.String(128), nullable=True)  # ISBN, barcode, etc.
    # optional links
    external_url = db.Column(db.String(512), nullable=True)
    image_url = db.Column(db.String(512), nullable=True)

    # relationships: authors and genres (many-to-many)
    authors = db.relationship('Author', secondary='item_author', backref='items')
    genres = db.relationship('Genre', secondary='item_genre', backref='items')

    __mapper_args__ = {
        'polymorphic_identity': 'item',
        'polymorphic_on': type
    }


# Association tables for many-to-many relationships
item_author = db.Table(
    'item_author',
    db.Column('item_id', db.Integer, db.ForeignKey('item.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True),
)

item_genre = db.Table(
    'item_genre',
    db.Column('item_id', db.Integer, db.ForeignKey('item.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True),
)


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)


class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

# add relationships on Item


class Book(Item):
    __tablename__ = 'book'
    id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
    # Book-specific
    language = db.Column(db.String(32), nullable=False)
    publisher = db.Column(db.String(120), nullable=True)
    length = db.Column(db.Integer, nullable=True)  # number of pages
    size = db.Column(db.String(64), nullable=True)  # dimensions or file size

    __mapper_args__ = {
        'polymorphic_identity': 'book',
    }


class CD(Item):
    __tablename__ = 'cd'
    id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
    # CD-specific
    primary_artist = db.Column(db.String(120), nullable=False)
    publisher = db.Column(db.String(120), nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    track_list = db.Column(db.JSON, nullable=True)
    genre = db.Column(db.String(120), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'cd',
    }


class DVD(Item):
    __tablename__ = 'dvd'
    id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
    # DVD-specific
    director = db.Column(db.String(120), nullable=True)
    main_actors = db.Column(db.Text, nullable=True)
    genre = db.Column(db.String(120), nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'dvd',
    }


class BoardGame(Item):
    __tablename__ = 'board_game'
    id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
    # Board game specific
    author_note = db.Column(db.String(120), nullable=True)
    min_players = db.Column(db.Integer, nullable=True)
    max_players = db.Column(db.Integer, nullable=True)
    genre = db.Column(db.String(120), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'board_game',
    }
