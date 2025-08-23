import os
from flask import Flask, render_template, request, send_file, jsonify
from dotenv import load_dotenv
from models import db, Song, USSong
from index import index_songs
from sqlalchemy.orm import class_mapper

load_dotenv()

SONGFOLDER = os.getenv('SONGFOLDER')
SONG_DB = os.getenv('SONG_DB')
ULTRASTAR_DB = os.getenv('ULTRASTAR_DB')
QR_URL = os.getenv('QR_URL')


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = SONG_DB
    app.config['SQLALCHEMY_BINDS'] = {'us_db': ULTRASTAR_DB}
    db.init_app(app)

    with app.app_context():
        # index songs on startup
        index_songs()

    return app


app = create_app()


def model_to_dict(model):
    """Convert SQLAlchemy model to dict"""
    if isinstance(model, list):
        return [model_to_dict(m) for m in model]
    columns = [c.key for c in class_mapper(model.__class__).columns]
    return {c: getattr(model, c) for c in columns}


def handle_song_request(request):
    artist_filter = request.args.get('artist_filter')
    song_filter = request.args.get('song_filter')
    sort_by = request.args.get('sort_by', 'artist')
    limit = request.args.get('limit', 1000)
    offset = request.args.get('offset', 0)

    query = Song.query

    if artist_filter:
        query = query.filter(Song.artist.like(f"%{artist_filter}%"))
    if song_filter:
        query = query.filter(Song.title.like(f"%{song_filter}%"))

    if sort_by == 'artist':
        query = query.order_by(Song.artist)
    elif sort_by == 'title':
        query = query.order_by(Song.title)
    elif sort_by == 'year':
        query = query.order_by(Song.year)

    if sort_by != 'times_played':
        query = query.limit(limit).offset(offset)

    songs = [model_to_dict(s) for s in query.all()]

    # Add TimesPlayed from USSong
    us_songs = [model_to_dict(s) for s in USSong.query.all()]
    for song in songs:
        match_found = False
        for us_song in us_songs:
            if us_song["artist"].rstrip('\x00') == song["artist"] and \
               us_song["title"].rstrip('\x00') == song["title"]:
                song["times_played"] = us_song["TimesPlayed"]
                match_found = True
                break
        if not match_found:
            song["times_played"] = 0

    if sort_by == 'times_played':
        songs = [s for s in songs if s['times_played'] > 0]
        songs = sorted(songs, key=lambda k: k['times_played'], reverse=True)

    return songs


@app.route('/')
def index():
    songs = handle_song_request(request)
    artist_filter = request.args.get('artist_filter', default='')
    song_filter = request.args.get('song_filter', default='')
    sort_by = request.args.get('sort_by', 'artist')
    return render_template('index.html', songs=songs,
                           artist_filter=artist_filter,
                           song_filter=song_filter,
                           sort_by=sort_by,
                           local_ip=QR_URL)


@app.route('/api/songs')
def api_songs():
    search = request.args.get('search', '').strip()
    query = Song.query
    if search:
        like_search = f"%{search}%"
        query = query.filter(
            (Song.artist.ilike(like_search)) |
            (Song.title.ilike(like_search)) |
            (Song.year.cast(db.String).ilike(like_search))
        )
    songs = query.order_by(Song.artist, Song.title).limit(100).all()
    result = [{
        "artist": s.artist,
        "title": s.title,
        "year": s.year,
        "times_played": s.times_played,
        "mp3_path": s.mp3_path
    } for s in songs]
    return jsonify({"songs": result})


@app.route('/api/mp3')
def api_mp3():
    mp3_path = request.args.get('mp3_path')
    mp3_path = os.path.join(SONGFOLDER, mp3_path)
    return send_file(mp3_path, mimetype='audio/mp3')


if __name__ == '__main__':
    app.run(debug=True)
