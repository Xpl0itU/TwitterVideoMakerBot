import os
import random
import json
import yt_dlp

def download_background() -> str:
    with open("data/videos.json", "r") as f:
        data = json.load(f)
        filename, link = random.choice(list(data.items()))
        filename += ".mp4"
        os.makedirs("./assets/backgrounds/", exist_ok=True)
        if os.path.exists(f"assets/backgrounds/{filename}"):
            return filename
        print("Downloading the background videos...")
        ydl_opts = {
            "format": "bestvideo[height<=1080][ext=mp4]",
            "outtmpl": f"assets/backgrounds/{filename}",
            "retries": 10,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(link)
        print("Background video downloaded successfully!")
        return filename