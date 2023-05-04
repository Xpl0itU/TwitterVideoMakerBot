import os
import random
import yt_dlp
import math
from flask_socketio import emit
import tempfile
from video_processing.user_data import get_user_data_dir

videos = {
    "minecraft": "https://www.youtube.com/watch?v=n_Dv4JMiwK8",
    "csgo": "https://www.youtube.com/watch?v=SNHDZlVxuYc",
    "fall_guys": "https://www.youtube.com/watch?v=0ifS1fBWpWc"
}

def report_progress(d):
    if d.get("status") == "downloading":
        total_bytes = d.get("total_bytes_estimate")
        downloaded_bytes = d.get("downloaded_bytes")
        if total_bytes and downloaded_bytes:
            emit('progress', {'progress': math.floor(downloaded_bytes / total_bytes * 100)}, broadcast=True)

def download_background() -> str:
    filename, link = random.choice(list(videos.items()))
    filename += ".mp4"
    os.makedirs(f"{get_user_data_dir()}/assets/backgrounds/", exist_ok=True)
    if os.path.exists(f"{get_user_data_dir()}/assets/backgrounds/{filename}"):
        return filename

    print("Downloading the background video...")
    emit('stage', {'stage': 'Downloading the background video'}, broadcast=True)

    ydl_opts = {
        "format": "bestvideo[height<=1080][ext=mp4]",
        "outtmpl": f"{get_user_data_dir()}/assets/backgrounds/{filename}",
        "retries": 10,
        "progress_hooks": [report_progress],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(link)
    print("Background video downloaded successfully!")
    return filename