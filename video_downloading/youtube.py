import os
import random
import json
import yt_dlp
import math
from flask_socketio import emit

def report_progress(d):
    if d.get("status") == "downloading":
        total_bytes = d.get("total_bytes_estimate")
        downloaded_bytes = d.get("downloaded_bytes")
        if total_bytes and downloaded_bytes:
            emit('progress', {'progress': math.floor(downloaded_bytes / total_bytes * 100)}, broadcast=True)

def download_background() -> str:
    with open("data/videos.json", "r") as f:
        data = json.load(f)
        filename, link = random.choice(list(data.items()))
        filename += ".mp4"
        os.makedirs("./assets/backgrounds/", exist_ok=True)
        if os.path.exists(f"assets/backgrounds/{filename}"):
            return filename

        print("Downloading the background video...")
        emit('stage', {'stage': 'Downloading the background video'}, broadcast=True)

        ydl_opts = {
            "format": "bestvideo[height<=1080][ext=mp4]",
            "outtmpl": f"assets/backgrounds/{filename}",
            "retries": 10,
            "progress_hooks": [report_progress],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(link)
        print("Background video downloaded successfully!")
        return filename