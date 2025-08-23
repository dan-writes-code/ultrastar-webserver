from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Song(db.Model):
    __tablename__ = 'songs'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    artist = db.Column(db.String(255))
    language = db.Column(db.String(255))
    year = db.Column(db.Integer)
    mp3_path = db.Column(db.String(255), unique=True)
    modify_date = db.Column(db.Integer)
    folder_path = db.Column(db.String(255))


class USSong(db.Model):
    __bind_key__ = 'us_db'
    __tablename__ = 'us_songs'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    artist = db.Column(db.String(255))
    title = db.Column(db.String(255))
    TimesPlayed = db.Column(db.Integer)
