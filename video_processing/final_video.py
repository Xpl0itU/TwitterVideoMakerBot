import os
import shutil
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
from twitter.tweet import TweetManager
from random import randrange
from typing import Tuple
from video_downloading.youtube import download_background
import tempfile
from video_processing.user_data import get_user_data_dir
from text_splitter.splitter import get_text_clip_for_tweet

import sys
from flask_socketio import emit
from video_processing.logger import MoviePyLogger
from playwright.async_api import async_playwright
import math

import operator
from functools import reduce


def flatten(lst: list) -> list:
    return reduce(operator.add, lst)


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
def create_video_clip_with_text_only(text: str, id: int, audio_path: str) -> VideoClip:
    return get_text_clip_for_tweet(text, id, audio_path)


# https://twitter.com/MyBetaMod/status/1641987054446735360?s=20
# https://twitter.com/jack/status/20?lang=en
async def generate_video(links: list, text_only=False) -> None:
    """
    Generates a video from a list of links to twitter statuses.
    """
    links = list(filter(lambda x: x != "", links))
    if len(links) == 0 or links is None or links == [] or links == [""]:
        emit(
            "stage",
            {"stage": "Error: No links provided, please reload the page and try again"},
            broadcast=True,
        )
        return
    tweets_in_threads = flatten(
        list(
            map(
                lambda x: TweetManager(int(x)).get_thread_tweets(),
                list(map(lambda x: re.search(r"/status/(\d+)", x).group(1), links)),
            )
        )
    )
    output_dir = f"{tempfile.gettempdir()}/Fudgify/results/{tweets_in_threads[0].id}"
    temp_dir = f"{tempfile.gettempdir()}/Fudgify/temp/{tweets_in_threads[0].id}"

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    video_clips = list()
    tweets_text = list()
    emit(
        "stage",
        {"stage": "Screenshotting tweets and generating the voice"},
        broadcast=True,
    )

    if text_only:
        tweets_text = list(
            map(
                lambda x: TweetManager(x.id).get_audio_from_tweet(temp_dir),
                tweets_in_threads,
            )
        )
    else:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()
            for i in range(len(tweets_in_threads)):
                # Twitter doesn't care about usernames
                thread_item_link = (
                    f"https://twitter.com/jack/status/{tweets_in_threads[i].id}"
                )
                if (
                    await TweetManager(
                        tweets_in_threads[i].id
                    ).get_audio_video_from_tweet(page, thread_item_link, temp_dir)
                    is False
                ):
                    return
                emit(
                    "progress",
                    {"progress": math.floor(i / len(tweets_in_threads) * 100)},
                    broadcast=True,
                )

            await browser.close()

    emit("stage", {"stage": "Creating clips for each tweet"}, broadcast=True)
    for i in range(len(tweets_in_threads)):
        video_clips.append(
            create_video_clip_with_text_only(
                tweets_text[i],
                tweets_in_threads[i].id,
                f"{temp_dir}/{tweets_in_threads[i].id}.mp3",
            )
            if text_only
            else create_video_clip(
                f"{temp_dir}/{tweets_in_threads[i].id}.mp3",
                f"{temp_dir}/{tweets_in_threads[i].id}.png",
            )
        )
        emit(
            "progress",
            {"progress": math.floor(i / len(tweets_in_threads) * 100)},
            broadcast=True,
        )

    tweets_clip = concatenate_videoclips(
        video_clips, "compose", bg_color=None, padding=0
    ).set_position("center")
    background_filename = (
        f"{get_user_data_dir()}/assets/backgrounds/{download_background()}"
    )
    background_clip = VideoFileClip(background_filename)
    tweets_clip = tweets_clip.fx(vfx.speedx, 1.1)  # type: ignore
    start_time, end_time = get_start_and_end_times(
        tweets_clip.duration, background_clip.duration
    )
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
        f"{output_dir}/Fudgify-{tweets_in_threads[0].id}.webm",
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
    shutil.rmtree(f"{tempfile.gettempdir()}/Fudgify/temp")
    emit("stage", {"stage": "Video generated, ready to download"}, broadcast=True)
    emit("done", {"done": None}, broadcast=True)


def get_exported_video_path(link: str) -> str:
    id = re.search(r"/status/(\d+)", link).group(1)
    return f"{tempfile.gettempdir()}/Fudgify/results/{id}/Fudgify-{id}.webm"
