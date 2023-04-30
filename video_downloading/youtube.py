import os
import random
import json
import yt_dlp
from flask_socketio import emit

def progress_hooks(d):
    try:
        if d["status"] == "downloading":
            emit('progress', {'progress': int(d["downloaded_bytes"]) / int(d["total_bytes"]) * 100}, broadcast=True)
    except Exception as e:
        pass

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
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(link)
        print("Background video downloaded successfully!")
        return filename