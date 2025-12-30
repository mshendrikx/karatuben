import os
import time
import logging
import subprocess
import dotenv

from pytubefix import YouTube
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

dotenv.load_dotenv()

YT_BASE_URL = "https://www.youtube.com/watch?v="
DOWNLOAD_FOLDER = "/app/downloads"
OUTPUT_FOLDER = "/app/songs"
TARGET_LUFS = os.getenv("TARGET_LUFS", "-16")
LOG_LEVEL = os.getenv("LOG_LEVEL", "NOTSET")

db = SQLAlchemy()


class Song(db.Model):
    youtubeid = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100))
    artist = db.Column(db.String(100))
    downloaded = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )


if LOG_LEVEL == "DEBUG":
    log_level = logging.DEBUG
elif LOG_LEVEL == "INFO":
    log_level = logging.INFO
elif LOG_LEVEL == "WARN":
    log_level = logging.WARN
elif LOG_LEVEL == "ERROR":
    log_level = logging.ERROR
elif LOG_LEVEL == "FATAL":
    log_level = logging.FATAL
else:
    log_level = logging.NOTSET

logging.basicConfig(
    filename="/app/logs/karatuben.log",
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create a logger
logger = logging.getLogger(__name__)


def normalize_video(filename):

    input_path = os.path.join(DOWNLOAD_FOLDER, filename)
    output_path = os.path.join(OUTPUT_FOLDER, filename)

    command = [
        "ffmpeg-normalize",
        input_path,
        "-c:a",
        "aac",
        "-b:a",
        "256k",
        "-nt",
        "ebu",
        "-t",
        TARGET_LUFS,
        "-o",
        output_path,
    ]

    try:
        # Run the command and hide the massive wall of text FFmpeg usually spits out
        # capture_output=True keeps your terminal clean.
        subprocess.run(command, check=True, capture_output=True)

    except subprocess.CalledProcessError as e:
        logger.error(f"   -> ERROR processing {filename}.")
        # Print the specific error from FFmpeg if it fails
        logger.error(f"   Error details: {e.stderr.decode()}")

        # Delete the original file
        os.remove(input_path)

        return False

    # Delete the original file
    os.remove(input_path)

    return True


logger.info("Starting Karatuben.")

app = Flask(__name__)

db_user = os.environ.get("MYSQL_USER", "root")
db_pass = os.environ.get("MYSQL_ROOT_PASSWORD")
db_host = os.environ.get("MYSQL_HOST")
db_port = os.environ.get("MYSQL_PORT", "3306")
db_name = os.environ.get("MYSQL_DATABASE", "karatube")
db_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
db.init_app(app)

with app.app_context():

    while 1 == 1:

        songs = Song.query.filter_by(downloaded=0)
        for song in songs:
            video_file = str(song.youtubeid) + ".mp4"
            video_path = DOWNLOAD_FOLDER
            download_url = YT_BASE_URL + str(song.youtubeid)
            try:
                logger.info("Downloading video: " + song.artist + " - " + song.name)
                YouTube(download_url).streams.first().download(
                    output_path=video_path, filename=video_file
                )
                logger.info("Video: " + song.artist + " - " + song.name + " downloaded")
                time.sleep(int(os.environ.get("TIME_SLEEP")))

            except Exception as e:
                logger.error("Error downloading video: " + e.error_string)
                continue

            logger.info("Video: " + song.artist + " - " + song.name + " normalizing.")
            if normalize_video(video_file) == True:
                time.sleep(int(os.environ.get("TIME_SLEEP")))
                logger.info(
                    "Video: " + song.artist + " - " + song.name + " normalized."
                )
                updated_song = Song.query.filter_by(youtubeid=song.youtubeid).first()
                updated_song.downloaded = 1
                db.session.commit()
            else:
                logger.error(
                    "Video: " + song.artist + " - " + song.name + " not normalized."
                )

        time.sleep(int(os.environ.get("TIME_SLEEP")))
