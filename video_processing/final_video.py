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
from playwright.sync_api import sync_playwright
import math

import operator
from functools import reduce

from ffmpeg_progress_yield import FfmpegProgress, ffmpeg_progress_yield

from video_processing.subtitles import transcribe_audio


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
    random_time = randrange(180, int(float(length_of_clip)) - int(video_length))
    return random_time, random_time + video_length


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
    audio_clips = list()
    tweets_text = list()
    audio_lengths = list()
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
    screenshot_width = int((1080 * 45) // 100)
    for i in range(len(tweets_in_threads)):
        if not text_only:
            video_clips.append(
                ffmpeg.input(
                    f"{temp_dir}/{tweets_in_threads[i].id}.png",
                ).filter("scale", screenshot_width, -1)
            )
        audio_clips.append(
            ffmpeg.input(
                f"{temp_dir}/{tweets_in_threads[i].id}.mp3",
            )
        )
        audio_lengths.append(
            float(
                ffmpeg.probe(f"{temp_dir}/{tweets_in_threads[i].id}.mp3")["format"][
                    "duration"
                ]
            )
        )
        emit(
            "progress",
            {"progress": math.floor(i / len(tweets_in_threads) * 100)},
            broadcast=True,
        )

    audio_concat = ffmpeg.concat(*audio_clips, a=1, v=0)
    ffmpeg.output(
        audio_concat,
        f"{temp_dir}/audio.mp3",
        **{"b:a": "192k"},  # Build full audio to get more accurate subtitles
    ).overwrite_output().run(quiet=True)

    background_filename = (
        f"{get_user_data_dir()}/assets/backgrounds/{download_background()}"
    )

    video_duration = sum(audio_lengths)

    start_time, end_time = get_start_and_end_times(
        video_duration,
        ffmpeg.probe(background_filename)["format"]["duration"],
    )

    background_clip = (
        ffmpeg.input(background_filename)
        .trim(
            start=start_time,
            end=end_time,
        )
        .filter("crop", "ih*(1080/1920)", "ih")
        .filter("setpts", "PTS-STARTPTS")
        .filter("fifo")
    )

    current_time = 0
    if text_only:
        for i in range(len(tweets_text)):
            background_clip, current_time = get_text_clip_for_tweet(
                tweets_text[i], tweets_in_threads[i].id, background_clip, current_time
            )
    else:
        for i in range(len(video_clips)):
            background_clip = ffmpeg.filter(
                [background_clip, video_clips[i]],
                "overlay",
                enable=f"between(t,{current_time},{current_time + audio_lengths[i]})",
                x="(main_w-overlay_w)/2",
                y="(main_h-overlay_h)/2",
            )
            current_time += audio_lengths[i]

    # Generate subtitles timestamp for each audio
    emit("stage", {"stage": "Generating Subtitles"}, broadcast=True)
    transcribe_audio(
        f"{temp_dir}/audio.mp3", f"{temp_dir}/subtitles.srt"
    )  # Export the subtitle for subtitles.str

    emit("stage", {"stage": "Rendering final video"}, broadcast=True)
    # Append subtitles for each audio
    background_clip = background_clip.filter(
        "subtitles",
        f"{temp_dir}/subtitles.srt",  # Declare this filter as subtitles filter and give your path
        force_style="Fontsize=18,"
        "PrimaryColour=&HFFFFFF&,"  # Font Color in BGR format or ABGR format
        "OutlineColour=&H40000000,"  # Outline Color from font
        "Alignment=6,"  # Top Center Alignment
        "MarginL=0,"  # Offset Left
        "MarginR=0,"  # Offset Right
        "MarginV=200",  # Vertical Offset
    )
    cmd = (
        ffmpeg.output(
            background_clip,
            audio_concat,
            f"{output_dir}/Fudgify-{tweets_in_threads[0].id}.mp4",
            f="mp4",
            **{
                "c:v": "h264",
                "b:v": "20M",
                "b:a": "128k",
                "threads": multiprocessing.cpu_count(),
            },
        )
        .overwrite_output()
        .compile()
    )

    ffmpeg_progress = FfmpegProgress(cmd)
    for progress in ffmpeg_progress.run_command_with_progress():
        emit("progress", {"progress": progress}, broadcast=True)

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
    return f"{tempfile.gettempdir()}/Fudgify/results/{id}/Fudgify-{id}.mp4"
