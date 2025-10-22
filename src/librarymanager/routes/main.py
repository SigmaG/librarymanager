from flask import Blueprint, render_template, request, redirect, url_for, current_app, abort
from ..models import Item, Author, Genre, Book, CD, DVD, BoardGame
from ..extensions import db
from sqlalchemy import tuple_
import json

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    # server-rendered homepage showing recent items
    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    items = Item.query.order_by(Item.id.desc()).limit(per_page).all()
    return render_template('index.html', items=items)


@main_bp.route('/items/<int:item_id>')
def item_detail(item_id: int):
    it = Item.query.get_or_404(item_id)
    return render_template('item_detail.html', item=it)


@main_bp.route('/items/new')
def new_item_index():
    # choose type
    return render_template('forms/new_item_index.html')


@main_bp.route('/items/type/<typ>')
def items_by_type(typ: str):
    # show all items of a given type
    typ = typ.lower()
    # map common route values to the polymorphic identity stored in the DB
    mapping = {
        'book': 'book',
        'cd': 'cd',
        'dvd': 'dvd',
        'boardgame': 'board_game',
        'board_game': 'board_game',
    }
    db_type = mapping.get(typ, typ)
    # pagination
    # cursor-based bidirectional pagination and sorting
    sort = request.args.get('sort', 'id')
    order = request.args.get('order', 'asc')
    cursor = request.args.get('cursor')
    direction = request.args.get('direction', 'next')  # 'next' or 'prev'
    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)

    from base64 import urlsafe_b64encode, urlsafe_b64decode

    def encode_cursor_obj(obj) -> str:
        s = json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
        return urlsafe_b64encode(s.encode()).decode()

    def decode_cursor_obj(token: str):
        try:
            txt = urlsafe_b64decode(token.encode()).decode()
            return json.loads(txt)
        except Exception:
            abort(400, description='Invalid cursor token')

    query = Item.query.filter_by(type=db_type)
    order_col = Item.title if sort == 'title' else Item.id
    # secondary tiebreaker is id for stable ordering
    sec_col = Item.id

    # build comparison based on requested direction
    if not cursor:
        # initial page
        if order == 'desc':
            q = query.order_by(order_col.desc())
        else:
            q = query.order_by(order_col.asc())
        items_raw = q.limit(per_page + 1).all()
        # display items in order requested
        items_display = items_raw[:per_page]
        if order == 'desc':
            # items_raw already in desc order; display as-is
            pass
    else:
        # decode composite cursor
        cur_obj = decode_cursor_obj(cursor)
        cur_val = None
        cur_title = None
        cur_id = None
        if sort == 'id':
            if not isinstance(cur_obj, dict) or 'id' not in cur_obj:
                abort(400, description='Cursor missing id')
            try:
                cur_id = int(cur_obj['id'])
            except Exception:
                abort(400, description='Invalid id in cursor')
        else:
            if not isinstance(cur_obj, dict) or 'title' not in cur_obj or 'id' not in cur_obj:
                abort(400, description='Cursor missing title/id')
            cur_title = cur_obj['title']
            try:
                cur_id = int(cur_obj['id'])
            except Exception:
                abort(400, description='Invalid id in cursor')

        if direction == 'next':
            if sort == 'id':
                comp = order_col > cur_id if order == 'asc' else order_col < cur_id
            else:
                comp = tuple_(order_col, sec_col) > (cur_title, cur_id) if order == 'asc' else tuple_(order_col, sec_col) < (cur_title, cur_id)
            q = query.filter(comp)
            q = q.order_by(order_col.asc() if order == 'asc' else order_col.desc())
            items_raw = q.limit(per_page + 1).all()
            items_display = items_raw[:per_page]
        else:  # direction == 'prev'
            # to fetch previous page, query the opposite side and then reverse
            if sort == 'id':
                comp = order_col < cur_id if order == 'asc' else order_col > cur_id
            else:
                comp = tuple_(order_col, sec_col) < (cur_title, cur_id) if order == 'asc' else tuple_(order_col, sec_col) > (cur_title, cur_id)
            # fetch in reverse order
            q = query.filter(comp)
            q = q.order_by(order_col.desc() if order == 'asc' else order_col.asc())
            items_raw = q.limit(per_page + 1).all()
            items_display = list(reversed(items_raw[:per_page]))

    # compute cursors
    has_next = False
    has_prev = False
    next_cursor = None
    prev_cursor = None
    if items_display:
        # determine prev and next cursor objects
        first = items_display[0]
        last = items_display[-1]
        if sort == 'id':
            prev_cursor = encode_cursor_obj({'id': getattr(first, 'id')})
            next_cursor = encode_cursor_obj({'id': getattr(last, 'id')})
        else:
            prev_cursor = encode_cursor_obj({'title': getattr(first, 'title'), 'id': getattr(first, 'id')})
            next_cursor = encode_cursor_obj({'title': getattr(last, 'title'), 'id': getattr(last, 'id')})

    # determine has_next/has_prev from items_raw length and presence of cursor
    if 'items_raw' in locals():
        if len(items_raw) > per_page:
            if direction == 'next' or not cursor:
                has_next = True
            else:
                has_prev = True
        # When cursor provided and direction==next, there may be previous pages
        if cursor:
            # if we fetched with > or < filter, then previous pages exist
            has_prev = True

    display_label = db_type.replace('_', ' ').capitalize()
    # total count for this type (useful for showing totals in UI)
    total = Item.query.filter_by(type=db_type).count()
    return render_template('item_list.html', items=items_display, type=display_label, route_param=typ, next_cursor=next_cursor, prev_cursor=prev_cursor, has_next=has_next, has_prev=has_prev, sort=sort, order=order, total=total)


@main_bp.route('/items/new/<typ>', methods=['GET', 'POST'])
def new_item(typ: str):
    typ = typ.lower()
    if request.method == 'GET':
        template = f'forms/new_{typ}.html'
        return render_template(template)

    # POST: create item from form
    form = request.form
    title = form.get('title') or 'Untitled'
    description = form.get('description')
    def _normalize_list(s: str):
        return list({x.strip().title() for x in (s or '').split(',') if x.strip()})

    authors = _normalize_list(form.get('authors'))
    genres = _normalize_list(form.get('genres'))

    if typ == 'book':
        language = form.get('language')
        publisher = form.get('publisher')
        length = form.get('length') or None
        size = form.get('size')
        obj = Book(title=title, description=description, language=language or None, publisher=publisher, length=int(length) if length else None, size=size)
    elif typ == 'cd':
        artist = form.get('artist')
        publisher = form.get('publisher')
        duration = form.get('duration') or None
        tracks = form.get('track_list')
        obj = CD(title=title, description=description, primary_artist=artist or None, publisher=publisher, duration_minutes=int(duration) if duration else None, track_list=[t.strip() for t in tracks.split(',')] if tracks else None)
    elif typ == 'dvd':
        director = form.get('director')
        main_actors = form.get('main_actors')
        duration = form.get('duration') or None
        obj = DVD(title=title, description=description, director=director, main_actors=main_actors, duration_minutes=int(duration) if duration else None)
    elif typ in ('boardgame', 'board_game'):
        author_note = form.get('author')
        min_players = form.get('min_players') or None
        max_players = form.get('max_players') or None
        obj = BoardGame(title=title, description=description, author_note=author_note, min_players=int(min_players) if min_players else None, max_players=int(max_players) if max_players else None)
    else:
        return 'Unknown type', 400

    # optional links from form
    obj.external_url = form.get('external_url') or None
    obj.image_url = form.get('image_url') or None

    # persist and attach authors/genres
    db.session.add(obj)
    db.session.flush()

    for a in authors:
        auth = Author.query.filter_by(name=a).first()
        if not auth:
            auth = Author(name=a)
            db.session.add(auth)
            db.session.flush()
        obj.authors.append(auth)

    for g in genres:
        gen = Genre.query.filter_by(name=g).first()
        if not gen:
            gen = Genre(name=g)
            db.session.add(gen)
            db.session.flush()
        obj.genres.append(gen)

    db.session.commit()
    return redirect(url_for('main.item_detail', item_id=obj.id))



@main_bp.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id: int):
    it = Item.query.get_or_404(item_id)
    if request.method == 'GET':
        # render the same form template but pass item to prefill
        template = f'forms/new_{it.type}.html'
        return render_template(template, item=it)

    form = request.form
    title = form.get('title') or it.title
    description = form.get('description')

    def _normalize_list(s: str):
        return list({x.strip().title() for x in (s or '').split(',') if x.strip()})

    authors = _normalize_list(form.get('authors'))
    genres = _normalize_list(form.get('genres'))

    # update fields based on type
    it.title = title
    it.description = description

    if it.type == 'book':
        it.language = form.get('language') or it.language
        it.publisher = form.get('publisher') or it.publisher
        length = form.get('length')
        it.length = int(length) if length else it.length
        it.size = form.get('size') or it.size
    elif it.type == 'cd':
        it.primary_artist = form.get('artist') or it.primary_artist
        it.publisher = form.get('publisher') or it.publisher
        dur = form.get('duration')
        it.duration_minutes = int(dur) if dur else it.duration_minutes
        tracks = form.get('track_list')
        it.track_list = [t.strip() for t in tracks.split(',')] if tracks else it.track_list
    elif it.type == 'dvd':
        it.director = form.get('director') or it.director
        it.main_actors = form.get('main_actors') or it.main_actors
        dur = form.get('duration')
        it.duration_minutes = int(dur) if dur else it.duration_minutes
    elif it.type == 'board_game':
        it.author_note = form.get('author') or it.author_note
        minp = form.get('min_players')
        maxp = form.get('max_players')
        it.min_players = int(minp) if minp else it.min_players
        it.max_players = int(maxp) if maxp else it.max_players

    # update authors and genres: clear and reattach
    it.authors.clear()
    it.genres.clear()
    for a in authors:
        auth = Author.query.filter_by(name=a).first()
        if not auth:
            auth = Author(name=a)
            db.session.add(auth)
            db.session.flush()
        it.authors.append(auth)

    for g in genres:
        gen = Genre.query.filter_by(name=g).first()
        if not gen:
            gen = Genre(name=g)
            db.session.add(gen)
            db.session.flush()
        it.genres.append(gen)

    db.session.commit()
    return redirect(url_for('main.item_detail', item_id=it.id))


@main_bp.route('/items/<int:item_id>/delete', methods=['POST'])
def delete_item(item_id: int):
    it = Item.query.get_or_404(item_id)
    db.session.delete(it)
    db.session.commit()
    return redirect(url_for('main.index'))
