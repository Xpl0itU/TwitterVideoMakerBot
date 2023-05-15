import asyncio
import os
import shutil
import argparse
import multiprocessing
from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    VideoClip,
    concatenate_videoclips,
    VideoFileClip,
    CompositeVideoClip,
    vfx,
)
import re
from twitter.tweet import get_thread_tweets, get_audio_video_from_tweet, get_audio_from_tweet, get_tweet
from random import randrange
from typing import Tuple
from video_downloading.youtube import download_background
import tempfile
from video_processing.user_data import get_user_data_dir
from text_splitter.splitter import get_text_clip_from_audio

import sys
from flask_socketio import emit
from video_processing.logger import MoviePyLogger
from playwright.async_api import async_playwright
import math


def flatten(lst: list) -> list:
    if isinstance(lst, list):
        return [item for sublist in lst for item in flatten(sublist)]
    return [lst]


def get_start_and_end_times(video_length: int, length_of_clip: int) -> Tuple[int, int]:
    random_time = randrange(180, int(length_of_clip) - int(video_length))
    return random_time, random_time + video_length


def create_video_clip(audio_path: str, image_path: str) -> ImageClip:
    audio_clip = AudioFileClip(audio_path)
    image_clip = ImageClip(image_path)
    image_clip = image_clip.set_audio(audio_clip)
    image_clip = image_clip.set_duration(audio_clip.duration)
    return image_clip.set_fps(1)

# TODO: Show media if the tweet contains it
def create_video_clip_with_text_only(text: str, id: int) -> VideoClip:
    return get_text_clip_from_audio(text, id)


async def generate_video(links: list, text_only=False) -> None:
    ids = list()
    for link in links:
        ids.append(re.search("/status/(\d+)", link).group(1))
    output_dir = f"{tempfile.gettempdir()}/results/{ids[0]}"
    temp_dir = f"{tempfile.gettempdir()}/temp/{ids[0]}"

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    tweets_in_threads = list()
    for i in range(len(ids)):
        tweets_in_threads.append(get_thread_tweets(ids[i]))
        # Fix for first tweet in thread not being added
        if tweets_in_threads[i][0].id != ids[i]:
            tweets_in_threads[i].insert(0, [get_tweet(ids[i])])
    # Flatten list of lists
    tweets_in_threads = flatten(tweets_in_threads)
    video_clips = list()
    tweet_ids = list()
    emit(
        "stage",
        {"stage": "Screenshotting tweets and generating the voice"},
        broadcast=True,
    )

    tweets_text = list()
    
    if text_only:
        for i in range(len(tweets_in_threads)):
            tweet_ids.append(tweets_in_threads[i].id)
            tweets_text.append(get_audio_from_tweet(
                tweets_in_threads[i].id, temp_dir
            ))
            emit(
                "progress",
                {"progress": math.floor(i / len(tweets_in_threads) * 100)},
                broadcast=True,
            )
    else:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()
            username = re.search("twitter.com/(.*?)/status", link).group(1)
            for i in range(len(tweets_in_threads)):
                tweet_ids.append(tweets_in_threads[i].id)
                thread_item_link = (
                    f"https://twitter.com/{username}/status/{tweets_in_threads[i].id}"
                )
                await get_audio_video_from_tweet(
                    page, thread_item_link, tweets_in_threads[i].id, temp_dir
                )
                emit(
                    "progress",
                    {"progress": math.floor(i / len(tweets_in_threads) * 100)},
                    broadcast=True,
                )

            await browser.close()

    emit("stage", {"stage": "Creating clips for each tweet"}, broadcast=True)
    for i in range(len(tweet_ids)):
        video_clips.append(
            create_video_clip_with_text_only(
                tweets_text[i], tweet_ids[i]
            ) if text_only else create_video_clip(
                f"{temp_dir}/{tweet_ids[i]}.mp3", f"{temp_dir}/{tweet_ids[i]}.png"
            )
        )
        emit(
            "progress",
            {"progress": math.floor(i / len(tweet_ids) * 100)},
            broadcast=True,
        )

    tweets_clip = concatenate_videoclips(
        video_clips, "compose", bg_color=None, padding=0
    ).set_position("center")
    tweets_clip = tweets_clip.set_position("center")
    background_filename = (
        f"{get_user_data_dir()}/assets/backgrounds/{download_background()}"
    )
    background_clip = VideoFileClip(background_filename)
    tweets_clip = tweets_clip.fx(vfx.speedx, 1.1)
    start_time, end_time = get_start_and_end_times(tweets_clip.duration, background_clip.duration)
    background_clip = background_clip.subclip(start_time, end_time)
    background_clip = background_clip.without_audio()
    background_clip = background_clip.resize(height=1920)
    c = background_clip.w // 2
    half_w = 1080 // 2
    x1 = c - half_w
    x2 = c + half_w
    background_clip = background_clip.crop(x1=x1, y1=0, x2=x2, y2=1920)
    screenshot_width = int((1080 * 90) // 100)
    tweets_clip = tweets_clip.resize(width=screenshot_width - 50)
    final_video = CompositeVideoClip([background_clip, tweets_clip])

    logger = MoviePyLogger()
    original_stderr = sys.stderr
    sys.stderr.write = logger.custom_stdout_write

    emit("stage", {"stage": "Rendering final video"}, broadcast=True)

    final_video.write_videofile(
        f"{output_dir}/Fudgify-{ids[0]}.webm",
        fps=24,
        remove_temp=True,
        threads=multiprocessing.cpu_count(),
        preset="ultrafast",
        temp_audiofile_path=tempfile.gettempdir(),
        codec="libvpx",
        bitrate="50000k",
        audio_bitrate="128k",
    )
    sys.stderr.write = original_stderr.write
    emit("stage", {"stage": "Cleaning up temporary files"}, broadcast=True)
    shutil.rmtree(f"{tempfile.gettempdir()}/temp")
    emit("stage", {"stage": "Video generated, ready to download"}, broadcast=True)
    emit("done", {"done": None}, broadcast=True)


def get_exported_video_path(link: str) -> str:
    id = re.search("/status/(\d+)", link).group(1)
    return f"{tempfile.gettempdir()}/results/{id}/Fudgify-{id}.webm"


# https://twitter.com/MyBetaMod/status/1641987054446735360?s=20
# https://twitter.com/jack/status/20?lang=en
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="TwitterVideoMakerBot",
        description="Generates a video from a thread of tweets",
    )
    parser.add_argument("tweet_link", nargs="?", type=str, help="Link of the tweet")
    args = parser.parse_args()
    if args.tweet_link is None:
        link = input("Link of the tweet: ")
    else:
        link = args.tweet_link
    asyncio.run(generate_video(link))
