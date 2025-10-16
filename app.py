import os
import time
import logging

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from pytubefix import YouTube
from dotenv import load_dotenv

load_dotenv()

ACTIVE_LOGGER = os.getenv("ACTIVE_LOGGER", "False")

if ACTIVE_LOGGER == "True":
    ACTIVE_LOGGER = True
else:
    ACTIVE_LOGGER = False

logging.basicConfig(filename='/app/logs/karatuben.log', level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create a logger
logger = logging.getLogger(__name__)

YT_BASE_URL = "https://www.youtube.com/watch?v="

Base = declarative_base()


class Song(Base):
    __tablename__ = "song"
    youtubeid = Column(String(100), primary_key=True)
    name = Column(String(100))
    artist = Column(String(100))
    downloaded = Column(Integer)


def get_session():

    try:
        mariadb_pass = os.environ.get("MYSQL_ROOT_PASSWORD")
        mariadb_host = os.environ.get("MYSQL_HOST")
        engine_string = (
            "mysql+pymysql://root:"
            + str(mariadb_pass)
            + "@"
            + str(mariadb_host)
            + "/karatube"
        )
        engine = create_engine(engine_string)
    except Exception as e:
        return None

    Session = sessionmaker(bind=engine)
    session = Session()

    return session


while 1 == 1:

    if ACTIVE_LOGGER:
        logger.info("Starting connection with db")
    session = get_session()
    
    if not session:
        if ACTIVE_LOGGER:
            logger.info("Error connecting to database")

    count = 0
    while count < 6:

        songs = session.query(Song).filter_by(downloaded=0)

        for song in songs:

            video_file = str(song.youtubeid) + ".mp4"
            video_path = "/app/songs"
            download_url = YT_BASE_URL + str(song.youtubeid)
            try:
                if ACTIVE_LOGGER:
                    logger.info("Downloading video: " + song.artist + " - " + song.name) 
                YouTube(download_url).streams.first().download(
                    output_path=video_path, filename=video_file
                )
            except Exception as e:
                if ACTIVE_LOGGER:
                    logger.info("Error downloading video: " + e.error_string)
                continue           
            
            if ACTIVE_LOGGER:
                logger.info("Video: " + song.artist + " - " + song.name + " downloaded") 
            song.downloaded = 1
            session.commit()

        time.sleep(int(os.environ.get("TIME_SLEEP")))
        count += 1
        
    if ACTIVE_LOGGER:
        logger.info("Closing connection with db")
        
    session.close()
