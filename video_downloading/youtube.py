import os
import random
import yt_dlp
from flask_socketio import emit
from video_processing.user_data import get_user_data_dir
import math

videos = {
    "minecraft": "https://www.youtube.com/watch?v=ZCPt78a1eLc",
    "minecraft-2": "https://www.youtube.com/watch?v=b_nJhnTQaZI",
    "minecraft-3": "https://www.youtube.com/watch?v=JPjwv8RHhMY",
    "subway": "https://www.youtube.com/watch?v=exoFKSWA1RM",
    "subway-2": "https://www.youtube.com/watch?v=uDE7YUJNPzs",
}


def report_progress(d) -> None:
    if d.get("status") == "downloading":
        total_bytes = d.get("total_bytes_estimate")
        downloaded_bytes = d.get("downloaded_bytes")
        if total_bytes and downloaded_bytes:
            emit(
                "progress",
                {"progress": math.floor(downloaded_bytes / total_bytes * 100)},
            )


def download_background() -> str:
    """
    Downloads a random background video
    :return: str, the name of the file with the extension
    """
    filename, link = random.choice(list(videos.items()))
    filename += ".mp4"
    backgrounds_folder_path = os.path.join(get_user_data_dir(), "assets", "backgrounds")
    os.makedirs(backgrounds_folder_path, exist_ok=True)
    background_path = os.path.join(backgrounds_folder_path, filename)
    if os.path.exists(background_path):
        return filename

    emit(
        "stage",
        {"stage": "Downloading the background video", "done": False},
    )

    ydl_opts = {
        "format": "bestvideo[height<=1080][ext=mp4]",
        "outtmpl": background_path,
        "retries": 10,
        "progress_hooks": [report_progress],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(link)
    return filename
