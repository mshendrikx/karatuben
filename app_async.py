import os
import logging
import pika

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from pytubefix import YouTube
from dotenv import load_dotenv

load_dotenv()

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

def callback(ch, method, properties, body):    

    #logger.info("Starting connection with db")
    session = get_session()
    song = session.query(Song).filter_by(youtubeid=body).first()
    if song:
        video_file = str(song.youtubeid) + ".mp4"
        video_path = "/app/songs"
        download_url = YT_BASE_URL + str(song.youtubeid)
        try:
            #logger.info("Downloading video: " + song.artist + " - " + song.name) 
            YouTube(download_url).streams.first().download(
                output_path=video_path, filename=video_file
            )
            song.downloaded = 1
            session.commit() 
            
        except Exception as e:
            1 == 1 
            
    session.close()

connection = pika.BlockingConnection(pika.ConnectionParameters(os.environ.get("RABBITMQ_HOST")))
channel = connection.channel()
channel.queue_declare(queue='youtube_download')
channel.basic_consume(queue='youtube_download',
                      auto_ack=True,
                      on_message_callback=callback)

channel.start_consuming()
