import os
from flask import current_app
from models import db, Song
from dotenv import load_dotenv

load_dotenv()
SONGFOLDER = os.getenv('SONGFOLDER')


def index_songs():
    """Index all songs in SONGFOLDER into the database"""
    with current_app.app_context():
        db.create_all()  # Create tables if they don't exist

        count = 0
        added = 0
        edited = 0

        for root, dirs, files in os.walk(SONGFOLDER):
            for file in files:
                if not file.endswith('.m4a'):
                    continue

                mp3_path = os.path.join(root, file).replace(SONGFOLDER, '').strip("/")

                # Find txt metadata in the same folder
                title = artist = language = year = None
                for folder_file in os.listdir(root):
                    if folder_file.endswith('.txt'):
                        try:
                            with open(os.path.join(root, folder_file), 'r', encoding='utf-8') as f:
                                for line in f.readlines()[:20]:
                                    if line.startswith('#TITLE:'):
                                        title = line.replace('#TITLE:', '').strip()
                                    elif line.startswith('#ARTIST:'):
                                        artist = line.replace('#ARTIST:', '').strip()
                                    elif line.startswith('#LANGUAGE:'):
                                        language = line.replace('#LANGUAGE:', '').strip()
                                    elif line.startswith('#YEAR:'):
                                        year = line.replace('#YEAR:', '').strip()
                        except UnicodeDecodeError:
                            with open(os.path.join(root, folder_file), 'r', encoding='ISO-8859-1') as f:
                                for line in f.readlines()[:20]:
                                    if line.startswith('#TITLE:'):
                                        title = line.replace('#TITLE:', '').strip()
                                    elif line.startswith('#ARTIST:'):
                                        artist = line.replace('#ARTIST:', '').strip()
                                    elif line.startswith('#LANGUAGE:'):
                                        language = line.replace('#LANGUAGE:', '').strip()
                                    elif line.startswith('#YEAR:'):
                                        year = line.replace('#YEAR:', '').strip()
                if not title or not artist:
                    continue

                modify_date = int(os.path.getmtime(root))
                folder_path = os.path.dirname(root.replace(SONGFOLDER, ''))

                existing = Song.query.filter_by(mp3_path=mp3_path).first()
                if existing:
                    existing.title = title
                    existing.artist = artist
                    existing.language = language
                    existing.year = year
                    existing.modify_date = modify_date
                    existing.folder_path = folder_path
                    edited += 1
                else:
                    new_song = Song(
                        title=title,
                        artist=artist,
                        language=language,
                        year=year,
                        mp3_path=mp3_path,
                        modify_date=modify_date,
                        folder_path=folder_path
                    )
                    db.session.add(new_song)
                    added += 1

                count += 1

        db.session.commit()
        print(f"Indexed {count} songs: {added} added, {edited} updated.")
