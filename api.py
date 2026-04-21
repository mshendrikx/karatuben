import os
import time
import logging
import subprocess
import dotenv

from pytubefix import YouTube
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify

dotenv.load_dotenv()

YT_BASE_URL = "https://www.youtube.com/watch?v="
DOWNLOAD_FOLDER = os.getenv("DOWNLOAD_FOLDER", "/app/downloads")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "/app/songs")
LOG_FOLDER = os.getenv("LOG_FOLDER", "/app/logs")
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
    filename=os.path.join(LOG_FOLDER, "karatuben.log"),
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create a logger
logger = logging.getLogger(__name__)

logger.info("Starting Karatuben.")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()

db_user = os.environ.get("MYSQL_USER", "root")
db_pass = os.environ.get("MYSQL_ROOT_PASSWORD")
db_host = os.environ.get("MYSQL_HOST")
db_port = os.environ.get("MYSQL_PORT", "3306")
db_name = os.environ.get("MYSQL_DATABASE", "karatube")
db_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
db.init_app(app)

logger.info("Karatuben started.")


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


@app.route("/api/download_karaoke", methods=["POST"])
def download_karaoke():

    data = request.get_json()

    # Basic validation: ensure title and author exist
    if not data or "youtubeid" not in data:
        return jsonify({"error": "Missing youtubeid"}), 400

    youtubeid = data["youtubeid"]

    video_file = str(youtubeid) + ".mp4"
    video_path = DOWNLOAD_FOLDER
    download_url = YT_BASE_URL + str(youtubeid)
    try:
        logger.info("Video: " + youtubeid + " - downloading.")
        YouTube(download_url).streams.first().download(
            output_path=video_path, filename=video_file
        )
        logger.info("Video: " + youtubeid + " - downloaded.")
    except Exception as e:
        logger.error("Error downloading video: " + str(e))
        return jsonify({"error": "Error downloading video"}), 500

    logger.info("Video: " + youtubeid + " - normalizing.")
    if normalize_video(video_file) == True:
        logger.info("Video: " + youtubeid + " - normalized.")
    else:
        logger.error("Video: " + youtubeid + " - failed.")

    return jsonify({"message": "Song added successfully", "youtubeid": youtubeid}), 201


if __name__ == "__main__":
    app.run(debug=True, port=5001, host="0.0.0.0")
