import os
import time
import logging
import subprocess
import shutil

from pathlib import Path
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
DOWNLOAD_FOLDER = "/app/downloads"
OUTPUT_FOLDER = "/app/songs"
TARGET_LUFS = -14

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
        mariadb_database = os.environ.get("MYSQL_DATABASE")
        engine_string = (
            "mysql+pymysql://root:"
            + str(mariadb_pass)
            + "@"
            + str(mariadb_host)
            + "/"
            + str(mariadb_database)
        )
        engine = create_engine(engine_string)
    except Exception as e:
        return None

    Session = sessionmaker(bind=engine)
    session = Session()

    return session

def normalize_video(filename):

    input_path = os.path.join(DOWNLOAD_FOLDER, filename)
    output_path = os.path.join(OUTPUT_FOLDER, filename)
    
    logger.info(f"Processing: {filename}...")    

    # Construct the FFmpeg command
    # We pass the command as a LIST of strings. This is safer and 
    # handles filenames with spaces (common in Karaoke) automatically.
    command = [
        "ffmpeg",
        "-y",                     # Overwrite output file without asking
        "-i", input_path,         # Input file
        "-c:v", "copy",           # Copy video stream (NO re-encoding)
        "-af", f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11", # Audio Filter
        output_path               # Output file
    ]
    try:
        # Run the command and hide the massive wall of text FFmpeg usually spits out
        # capture_output=True keeps your terminal clean.
        subprocess.run(command, check=True, capture_output=True)

        # Delete the original file
        os.remove(input_path)
                
    except subprocess.CalledProcessError as e:
        os.remove(input_path)
        logger.error(f"   -> ERROR processing {filename}.") 
        # Print the specific error from FFmpeg if it fails
        logger.error(f"   Error details: {e.stderr.decode()}")
 
        return False
    
    logger.info("Video" + filename + " normalized.")     
    return True

while 1 == 1:

    session = get_session()
    
    if not session:
        if ACTIVE_LOGGER:
            logger.info("Error connecting to database")

    count = 0
    while count < 6:

        songs = session.query(Song).filter_by(downloaded=0)

        for song in songs:

            video_file = str(song.youtubeid) + ".mp4"
            video_path = DOWNLOAD_FOLDER
            download_url = YT_BASE_URL + str(song.youtubeid)
            try:
                if ACTIVE_LOGGER:
                    logger.info("Downloading video: " + song.artist + " - " + song.name) 
                YouTube(download_url).streams.first().download(
                    output_path=video_path, filename=video_file
                )
            except Exception as e:
                if ACTIVE_LOGGER:
                    logger.error("Error downloading video: " + e.error_string)
                continue           
            
            if ACTIVE_LOGGER:
                logger.info("Video: " + song.artist + " - " + song.name + " downloaded") 
            song.downloaded = 1
            session.commit()
            
            normalize_video(video_file)

        time.sleep(int(os.environ.get("TIME_SLEEP")))
        count += 1
        
    session.close()
