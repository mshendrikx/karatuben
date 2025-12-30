import os
import subprocess

from pytubefix import YouTube
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from .models import Song
from . import db
from . import logger

main = Blueprint("main", __name__)

YT_BASE_URL = "https://www.youtube.com/watch?v="
DOWNLOAD_FOLDER = "/app/downloads"
OUTPUT_FOLDER = "/app/songs"
TARGET_LUFS = os.getenv("TARGET_LUFS", "-16")

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

@main.route("/getvideo/<youtubeid>")
def getvideo(youtubeid):
    
    video_file = str(youtubeid) + ".mp4"
    video_path = DOWNLOAD_FOLDER
    download_url = YT_BASE_URL + str(youtubeid)
    try:
        logger.info("Downloading video: " + str(youtubeid))
        YouTube(download_url).streams.first().download(
            output_path=video_path, filename=video_file
        )
        logger.info("Video: " + str(youtubeid) + " downloaded")
    except Exception as e:
        logger.error("Error downloading video: " + e.error_string)

    logger.info("Video: " + str(youtubeid) + " normalizing.")
    if normalize_video(video_file) == True:
        logger.info(
            "Video: " + str(youtubeid) + " normalized."
        )
        updated_song = Song.query.filter_by(youtubeid=youtubeid).first()
        updated_song.downloaded = 1
        db.session.commit()
    else:
        logger.error(
            "Video: " + str(youtubeid) + " not normalized."
        )

    


