from flask import Blueprint, jsonify, request
from ..models import Item, Book, CD, DVD, BoardGame
from ..extensions import db

api_bp = Blueprint('api', __name__)


@api_bp.route('/items', methods=['GET'])
def list_items():
    items = Item.query.all()
    result = []
    for it in items:
        base = {'id': it.id, 'type': it.type, 'title': it.title, 'description': it.description}
        base['external_url'] = getattr(it, 'external_url', None)
        base['image_url'] = getattr(it, 'image_url', None)
        # include authors and genres
        base['authors'] = [a.name for a in getattr(it, 'authors', [])]
        base['genres'] = [g.name for g in getattr(it, 'genres', [])]
        if isinstance(it, Book):
            base.update({'language': it.language, 'publisher': it.publisher, 'length': it.length, 'size': it.size})
        elif isinstance(it, CD):
            base.update({'primary_artist': it.primary_artist, 'publisher': it.publisher, 'duration_minutes': it.duration_minutes, 'track_list': it.track_list, 'genre': it.genre})
        elif isinstance(it, DVD):
            base.update({'director': it.director, 'main_actors': it.main_actors, 'genre': it.genre, 'duration_minutes': it.duration_minutes})
        elif isinstance(it, BoardGame):
            base.update({'author_note': it.author_note, 'min_players': it.min_players, 'max_players': it.max_players, 'genre': it.genre})
        result.append(base)
    return jsonify(result)


@api_bp.route('/items', methods=['POST'])
def create_item():
    data = request.get_json() or {}
    typ = (data.get('type') or 'book').lower()
    authors = data.get('authors') or []
    genres = data.get('genres') or []
    if typ == 'book':
        obj = Book(title=data.get('title', 'Untitled'), description=data.get('description'), language=data['language'] if 'language' in data else None, publisher=data.get('publisher'), length=data.get('length'), size=data.get('size'))
    elif typ == 'cd':
        obj = CD(title=data.get('title', 'Untitled'), description=data.get('description'), primary_artist=data.get('artist') or data.get('primary_artist'), publisher=data.get('publisher'), duration_minutes=data.get('duration_minutes'), track_list=data.get('track_list'), genre=data.get('genre'))
    elif typ == 'dvd':
        obj = DVD(title=data.get('title', 'Untitled'), description=data.get('description'), director=data.get('director'), main_actors=data.get('main_actors'), genre=data.get('genre'), duration_minutes=data.get('duration_minutes'))
    elif typ in ('board_game', 'boardgame', 'game'):
        obj = BoardGame(title=data.get('title', 'Untitled'), description=data.get('description'), author_note=data.get('author'), min_players=data.get('min_players'), max_players=data.get('max_players'), genre=data.get('genre'))
    else:
        return jsonify({'error': 'unknown type'}), 400

    # optional links (set on the object before relations)
    obj.external_url = data.get('external_url')
    obj.image_url = data.get('image_url')

    # attach authors and genres (create if missing)
    from ..models import Author, Genre

    # add the object to the session before appending relationships
    db.session.add(obj)
    db.session.flush()

    for a in authors:
        if not a:
            continue
        auth = Author.query.filter_by(name=a).first()
        if not auth:
            auth = Author(name=a)
            db.session.add(auth)
            db.session.flush()
        obj.authors.append(auth)

    for g in genres:
        if not g:
            continue
        gen = Genre.query.filter_by(name=g).first()
        if not gen:
            gen = Genre(name=g)
            db.session.add(gen)
            db.session.flush()
        obj.genres.append(gen)

    db.session.commit()
    return jsonify({'id': obj.id, 'type': obj.type, 'title': obj.title, 'authors': [a.name for a in obj.authors], 'genres': [g.name for g in obj.genres]}), 201
