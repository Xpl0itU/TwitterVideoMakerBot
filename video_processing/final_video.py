import asyncio
import os
import shutil
import argparse
import multiprocessing
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, VideoFileClip, CompositeVideoClip
import re
from twitter.tweet import get_thread_tweets, get_audio_video_from_tweet, get_tweet
from random import randrange
from typing import Tuple
from video_downloading.youtube import download_background
import tempfile
from video_processing.user_data import get_user_data_dir

import sys
from flask_socketio import emit
from video_processing.logger import MoviePyLogger
from playwright.async_api import async_playwright

def get_start_and_end_times(video_length: int, length_of_clip: int) -> Tuple[int, int]:
    random_time = randrange(180, int(length_of_clip) - int(video_length))
    return random_time, random_time + video_length

def create_video_clip(audio_path: str, image_path: str) -> ImageClip:
    audio_clip = AudioFileClip(audio_path)
    image_clip = ImageClip(image_path)
    image_clip = image_clip.set_audio(audio_clip)
    image_clip = image_clip.set_duration(audio_clip.duration)
    return image_clip.set_fps(1)

async def generate_video(link: str) -> None:
    id = re.search("/status/(\d+)", link).group(1)
    username = re.search("twitter.com/(.*?)/status", link).group(1)
    output_dir = f"{tempfile.gettempdir()}/results/{id}"
    temp_dir = f"{tempfile.gettempdir()}/temp/{id}"

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    tweets_in_thread = get_thread_tweets(id)
    # Fix for first tweet in thread not being added
    first_tweet = get_tweet(int(id))
    if tweets_in_thread[0] != first_tweet:
        tweets_in_thread.insert(0, first_tweet)
    video_clips = list()
    tweet_ids = list()
    emit('stage', {'stage': 'Screenshotting tweets and generating the voice'}, broadcast=True)
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        for i in range(len(tweets_in_thread)):
            tweet_ids.append(tweets_in_thread[i].id)
            thread_item_link = f"https://twitter.com/{username}/status/{tweets_in_thread[i].id}"
            await get_audio_video_from_tweet(page, thread_item_link, tweets_in_thread[i].id, f"{temp_dir}")
            emit('progress', {'progress': i / len(tweets_in_thread) * 100}, broadcast=True)
        
        await browser.close()
    
    emit('stage', {'stage': 'Creating clips for each tweet'}, broadcast=True)
    for i in range(len(tweet_ids)):
        video_clips.append(create_video_clip(f"{temp_dir}/{tweet_ids[i]}.mp3", f"{temp_dir}/{tweet_ids[i]}.png"))
        emit('progress', {'progress': i / len(tweet_ids) * 100}, broadcast=True)
    
    tweets_clip = concatenate_videoclips(video_clips, "compose", bg_color=None, padding=0).set_position(
        "center"
    )
    tweets_clip = tweets_clip.set_position("center")
    background_filename = f"{get_user_data_dir()}/assets/backgrounds/{download_background()}"
    background_clip = VideoFileClip(background_filename)
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
    tweets_clip = tweets_clip.resize(width=screenshot_width)
    final_video = CompositeVideoClip([background_clip, tweets_clip])

    logger = MoviePyLogger()
    original_stderr = sys.stderr
    sys.stderr.write = logger.custom_stdout_write

    emit('stage', {'stage': 'Rendering final video'}, broadcast=True)
    
    final_video.write_videofile(f"{output_dir}/Fudgify-{id}.mp4", fps=24, remove_temp=True, threads=multiprocessing.cpu_count(), preset="ultrafast", temp_audiofile_path=tempfile.gettempdir(), audio_codec='aac', codec='libx264', temp_audiofile='temp-audio.m4a')
    sys.stderr.write = original_stderr.write
    shutil.rmtree(f"{tempfile.gettempdir()}/temp")
    emit('stage', {'stage': 'Video generated, ready to export'}, broadcast=True)
    emit('done', {'done': None}, broadcast=True)

def get_exported_video_path(link: str) -> str:
    id = re.search("/status/(\d+)", link).group(1)
    return f"{tempfile.gettempdir()}/results/{id}/Fudgify-{id}.mp4"

# https://twitter.com/MyBetaMod/status/1641987054446735360?s=20
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='TwitterVideoMakerBot',
                    description='Generates a video from a thread of tweets')
    parser.add_argument('tweet_link', nargs='?', type=str, help='Link of the tweet')
    args = parser.parse_args()
    if args.tweet_link is None:
        link = input("Link of the tweet: ")
    else:
        link = args.tweet_link
    asyncio.run(generate_video(link))