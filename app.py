import os

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from pytubefix import YouTube

YT_BASE_URL = "https://www.youtube.com/watch?v="

Base = declarative_base()

class Song(Base):
    __tablename__ = 'song'
    youtubeid = Column(String(100), primary_key=True)
    name = Column(String(100))
    artist = Column(String(100))
    downloaded = Column(Integer)

def get_session():
    
    try:
        mariadb_pass = os.environ.get("MYSQL_ROOT_PASSWORD")
        mariadb_host = os.environ.get("MYSQL_HOST")
        engine_string = 'mysql+pymysql://root:' + str(mariadb_pass) + "@" + str(mariadb_host) + '/karatube'
        engine = create_engine(engine_string)
    except Exception as e:
        return None
    
    Session = sessionmaker(bind=engine)
    session = Session()

    return session



session = get_session()

songs = session.query(Song).filter_by(downloaded=0)

for song in songs:
    
    video_file = str(song.youtubeid) + ".mp4"
    video_path = '/app/karatube_songs'
    full_file = video_path +'/' + video_file
    if not os.path.exists(video_file):
        download_url = YT_BASE_URL + str(song.youtubeid)
        try:
            YouTube(download_url).streams.first().download(output_path=video_path ,filename=video_file)
        except Exception as e:
           continue

    
        

