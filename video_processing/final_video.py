import os
import shutil
import multiprocessing
from moviepy.editor import (
    VideoClip,
)
import ffmpeg
import re
from twitter.tweet import TweetManager
from random import randrange
from typing import Tuple
from video_downloading.youtube import download_background
import tempfile
from video_processing.user_data import get_user_data_dir
from text_splitter.splitter import get_text_clip_for_tweet

from flask_socketio import emit
from video_processing.logger import ProgressFfmpeg
from playwright.sync_api import sync_playwright
import math

import operator
from functools import reduce


def flatten(lst: list) -> list:
    """
    Flattens a list of lists.
    :param lst: The list to flatten.
    :return: The flattened list.
    """
    return list(reduce(operator.add, lst))


def get_start_and_end_times(video_length: int, length_of_clip: int) -> Tuple[int, int]:
    """
    Gets the start and end times for the video.
    :param video_length: The length of the video.
    :param length_of_clip: The length of the clip.
    :return: The start and end times.
    """
    random_time = randrange(180, int(float(length_of_clip)) - int(float(video_length)))
    return random_time, random_time + int(float(video_length))


def create_video_clip(audio_path: str, image_path: str):
    """
    Creates a video clip from the image and audio file.
    :param  audio_path: Path to the audio file.
    :param image_path: Path to the image file.
    :return: The video clip.
    """
    audio_clip = ffmpeg.input(audio_path)
    image_clip = ffmpeg.input(image_path, framerate=1)
    return ffmpeg.concat(image_clip, audio_clip, v=1, a=1)


# TODO: Show media if the tweet contains it
def create_video_clip_with_text_only(text: str, id: int, audio_path: str) -> VideoClip:
    """
    Creates a video clip from the text and audio file.
    :param text: The text of the tweet.
    :param id: The id of the tweet.
    :param audio_path: Path to the audio file.
    :return: The video clip.
    """
    return get_text_clip_for_tweet(text, id, audio_path)


# https://twitter.com/MyBetaMod/status/1641987054446735360?s=20
# https://twitter.com/jack/status/20?lang=en
def generate_video(links: list, text_only: bool = False) -> None:
    """
    Generates a video from a list of links to twitter statuses.
    :param links: A list of links to twitter statuses.
    :param text_only: Whether or not to only generate the text of the tweet.
    :return: None.
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
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            page = browser.new_page()
            for i in range(len(tweets_in_threads)):
                # Twitter doesn't care about usernames
                thread_item_link = (
                    f"https://twitter.com/jack/status/{tweets_in_threads[i].id}"
                )
                if (
                    TweetManager(tweets_in_threads[i].id).get_audio_video_from_tweet(
                        page, thread_item_link, temp_dir
                    )
                    is False
                ):
                    return
                emit(
                    "progress",
                    {"progress": math.floor(i / len(tweets_in_threads) * 100)},
                    broadcast=True,
                )

            browser.close()

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

    background_filename = (
        f"{get_user_data_dir()}/assets/backgrounds/{download_background()}"
    )
    background_clip = ffmpeg.input(background_filename)
    # tweets_clip = tweets_clip.fx(vfx.speedx, 1.1)  # type: ignore
    screenshot_width = int((1080 * 45) // 100)
    video_clips = list(
        map(
            lambda x: x.filter(
                "scale",
                w=screenshot_width,
                h=-2,
                force_original_aspect_ratio="decrease",
            ),
            video_clips,
        )
    )
    ffmpeg.concat(*video_clips).output(
        f"{temp_dir}/temp_tweets.webm",
        **{
            "c:v": "libvpx-vp9",
        },
    ).run(overwrite_output=True)
    start_time, end_time = get_start_and_end_times(
        ffmpeg.probe(f"{temp_dir}/temp_tweets.webm")["format"]["duration"],
        ffmpeg.probe(background_filename)["format"]["duration"],
    )
    tweets_clip = ffmpeg.input(f"{temp_dir}/temp_tweets.webm")
    final_video = (
        background_clip.overlay(
            tweets_clip,
            x="(main_w-overlay_w)/2",
            y="(main_h-overlay_h)/2",
        )
        .trim(start=start_time, end=end_time)
        .filter("crop", "ih*(1080/1920)", "ih")
    )

    emit("stage", {"stage": "Rendering final video"}, broadcast=True)

    progress = ProgressFfmpeg(
        int(float(ffmpeg.probe(f"{temp_dir}/temp_tweets.webm")["format"]["duration"])),
        lambda x: emit("progress", {"progress": int(x * 100)}, broadcast=True),
    )
    ffmpeg.output(
        final_video,
        f"{output_dir}/Fudgify-{tweets_in_threads[0].id}.webm",
        f="webm",
        **{
            "b:v": "50M",
            "b:a": "128k",
            "threads": multiprocessing.cpu_count(),
        },
    ).overwrite_output().global_args("-progress", progress.output_file.name).run(
        quiet=True,
        overwrite_output=True,
        capture_stdout=False,
        capture_stderr=False,
    )

    emit("progress", {"progress": 100}, broadcast=True)

    emit("stage", {"stage": "Cleaning up temporary files"}, broadcast=True)
    shutil.rmtree(f"{tempfile.gettempdir()}/Fudgify/temp")
    emit("stage", {"stage": "Video generated, ready to download"}, broadcast=True)
    emit("done", {"done": None}, broadcast=True)


def get_exported_video_path(link: str) -> str:
    """
    Gets the path to the exported video.
    :param link: The link to the twitter status.
    :return: The path to the exported video.
    """
    id = re.search(r"/status/(\d+)", link).group(1)
    return f"{tempfile.gettempdir()}/Fudgify/results/{id}/Fudgify-{id}.webm"
