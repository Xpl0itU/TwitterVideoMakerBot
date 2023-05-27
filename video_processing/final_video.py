import os
import shutil
import multiprocessing
import ffmpeg
import re
from twitter.tweet import TweetManager
from random import randrange
from typing import Tuple
from video_downloading.youtube import download_background
import tempfile
from video_processing.user_data import get_user_data_dir

from flask_socketio import emit
from playwright.sync_api import sync_playwright
import math

import operator
from functools import reduce

from ffmpeg_progress_yield import FfmpegProgress

from video_processing.subtitles import get_subtitles_style, transcribe_audio

modes = {
    "tweet screenshots + captions": {
        "show_captions": True,
        "show_first_tweet_screenshot": True,
        "show_rest_tweet_screenshots": True,
        "subtitles_style": 1,
    },
    "first tweet screenshot + captions": {
        "show_captions": True,
        "show_first_tweet_screenshot": True,
        "show_rest_tweet_screenshots": False,
        "subtitles_style": 1,
    },
    "only tweet screenshots": {
        "show_captions": False,
        "show_first_tweet_screenshot": True,
        "show_rest_tweet_screenshots": True,
        "subtitles_style": 0,
    },
    "only captions": {
        "show_captions": True,
        "show_first_tweet_screenshot": False,
        "show_rest_tweet_screenshots": False,
        "subtitles_style": 2,
    },
}


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
    initial_value = 180
    # Ensures that will be a valid interval in the video
    while int(length_of_clip) <= int(video_length + initial_value):
        if initial_value == initial_value // 2:
            raise Exception("Your background is too short for this video length")
        else:
            initial_value //= 2  # Divides the initial value by 2 until reach 0
    random_time = randrange(initial_value, int(length_of_clip) - int(video_length))
    return random_time, random_time + video_length


# https://twitter.com/MyBetaMod/status/1641987054446735360?s=20
# https://twitter.com/jack/status/20?lang=en
def generate_video(links: list, mode: str = "tweet screenshots + captions") -> None:
    """
    Generates a video from a list of links to twitter statuses.
    :param links: A list of links to twitter statuses.
    :param text_only: Whether or not to only generate the text of the tweet.
    :return: None.
    """
    mode_settings = modes.get(mode)
    if mode_settings is None:
        emit(
            "stage",
            {
                "stage": f"Error: Invalid mode '{mode}', please choose a valid mode",
                "done": False,
            },
        )
        return

    show_any_tweet_screenshots = (
        mode_settings["show_first_tweet_screenshot"]
        or mode_settings["show_rest_tweet_screenshots"]
    )
    text_only = mode_settings["show_captions"] and not show_any_tweet_screenshots
    only_first_tweet = (
        mode_settings["show_first_tweet_screenshot"]
        and not mode_settings["show_rest_tweet_screenshots"]
    )
    add_subtitles = (
        mode_settings["show_captions"] and mode_settings["subtitles_style"] != 0
    )

    links = [link for link in links if link != ""]
    if len(links) == 0 or links is None or links == [] or links == [""]:
        emit(
            "stage",
            {
                "stage": "Error: No links provided, please reload the page and try again",
                "done": False,
            },
        )
        return
    tweets_in_threads = flatten(
        [
            TweetManager(
                int(re.search(r"/status/(\d+)", link).group(1))
            ).get_thread_tweets()
            for link in links
        ]
    )
    output_dir = os.path.join(
        tempfile.gettempdir(), "Fudgify", "results", f"{tweets_in_threads[0].id}"
    )
    temp_dir = os.path.join(
        tempfile.gettempdir(), "Fudgify", "temp", f"{tweets_in_threads[0].id}"
    )

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    video_clips = []
    audio_clips = []
    audio_lengths = []
    emit(
        "stage",
        {"stage": "Screenshotting tweets and generating the voice", "done": False},
    )

    if show_any_tweet_screenshots:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            page = browser.new_page()
            for i in range(len(tweets_in_threads)):
                tweet = TweetManager(tweets_in_threads[i].id)
                tweet.get_audio_from_tweet(temp_dir)
                if i == 0 or not only_first_tweet:
                    if (
                        tweet.screenshot_tweet(
                            page,
                            os.path.join(temp_dir, f"{tweets_in_threads[i].id}.png"),
                        )
                        is False
                    ):
                        return
                emit(
                    "progress",
                    {"progress": math.floor(i / len(tweets_in_threads) * 100)},
                )

            browser.close()
    else:
        for i in range(len(tweets_in_threads)):
            if (
                TweetManager(tweets_in_threads[i].id).get_audio_from_tweet(temp_dir)
                is False
            ):
                return
            emit(
                "progress",
                {"progress": math.floor(i / len(tweets_in_threads) * 100)},
            )

    emit(
        "stage",
        {"stage": "Creating clips for each tweet", "done": False},
    )
    screenshot_width = int((1080 * 45) // 100)
    for i in range(len(tweets_in_threads)):
        if not text_only:
            # Only First tweet mode
            if i == 0 or not only_first_tweet:
                video_clips.append(
                    ffmpeg.input(
                        os.path.join(temp_dir, f"{tweets_in_threads[i].id}.png")
                    ).filter("scale", screenshot_width, -1)
                )
        audio_clips.append(
            ffmpeg.input(os.path.join(temp_dir, f"{tweets_in_threads[i].id}.mp3"))
        )
        audio_lengths.append(
            float(
                ffmpeg.probe(os.path.join(temp_dir, f"{tweets_in_threads[i].id}.mp3"))[
                    "format"
                ]["duration"]
            )
        )
        emit(
            "progress",
            {"progress": math.floor(i / len(tweets_in_threads) * 100)},
        )

    audio_concat = ffmpeg.concat(*audio_clips, a=1, v=0)
    ffmpeg.output(
        audio_concat,
        os.path.join(temp_dir, "temp-audio-subtitles.mp3"),
        **{
            "b:a": "192k",
            "threads": multiprocessing.cpu_count(),
        },  # Build full audio to get more accurate subtitles
    ).overwrite_output().run(quiet=True)

    background_filename = os.path.join(
        get_user_data_dir(), "assets", "backgrounds", download_background()
    )

    video_duration = sum(audio_lengths)

    start_time, end_time = get_start_and_end_times(
        video_duration,
        float(ffmpeg.probe(background_filename)["format"]["duration"]),
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

    if not text_only:
        current_time = 0
        for i in range(len(video_clips)):
            background_clip = ffmpeg.filter(
                [background_clip, video_clips[i]],
                "overlay",
                enable=f"between(t,{current_time},{current_time + audio_lengths[i]})",
                x="(main_w-overlay_w)/2",
                y="(main_h-overlay_h)/2",
            )
            current_time += audio_lengths[i]

    # Append subtitles for each audio
    if add_subtitles or text_only:
        # Generate subtitles timestamp for each audio
        emit(
            "stage",
            {"stage": "Generating Subtitles", "done": False},
        )
        transcribe_audio(
            os.path.join(temp_dir, "temp-audio-subtitles.mp3"),
            os.path.join(temp_dir, "temp-subtitles.srt"),
        )  # Export the subtitle for subtitles.str

        background_clip = background_clip.filter(
            "subtitles",
            os.path.join(
                temp_dir, "temp-subtitles.srt"
            ),  # Declare this filter as subtitles filter and give your path
            force_style=get_subtitles_style(
                desired_style=mode_settings["subtitles_style"]
            ),
        )
    emit(
        "stage",
        {"stage": "Rendering final video", "done": False},
    )
    cmd = (
        ffmpeg.output(
            background_clip,
            audio_concat,
            os.path.join(output_dir, f"Fudgify-{tweets_in_threads[0].id}.mp4"),
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
    for progress in ffmpeg_progress.run_command_with_progress(
        duration_override=video_duration
    ):
        emit(
            "progress",
            {"progress": progress},
        )

    shutil.rmtree(os.path.join(tempfile.gettempdir(), "Fudgify", "temp"))
    emit(
        "stage",
        {"stage": "Video generated, ready to download", "done": True},
        ignore_queue=True,
    )


def get_exported_video_path(link: str) -> str:
    """
    Gets the path to the exported video.
    :param link: The link to the twitter status.
    :return: The path to the exported video.
    """
    id = re.search(r"/status/(\d+)", link).group(1)
    return os.path.join(
        tempfile.gettempdir(), "Fudgify", "results", id, f"Fudgify-{id}.mp4"
    )
