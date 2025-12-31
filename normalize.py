import os
import subprocess

SOURCE_FOLDER = '/data/media/karaoke/songs'
DEST_FOLDER = '/data/media/karaoke/songs14'
TARGET_LUFS = "-14"

def normalize_video(filename):

    input_path = os.path.join(SOURCE_FOLDER, filename)
    output_path = os.path.join(DEST_FOLDER, filename)

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
        return False

    return True

file_names = os.listdir(SOURCE_FOLDER)

for file_name in file_names:
    normalize_video(file_name)