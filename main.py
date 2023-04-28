import asyncio
import os
import shutil
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
import re
from twitter.tweet import get_thread_tweets, get_audio_video_from_tweet
    
def create_video_clip(audio_path: str, image_path: str) -> ImageClip:
    audio_clip = AudioFileClip(audio_path)
    image_clip = ImageClip(image_path)
    image_clip = image_clip.set_audio(audio_clip)
    image_clip = image_clip.set_duration(audio_clip.duration)
    return image_clip.set_fps(60)

async def main(link: str) -> None:
    id = re.search("/status/(\d+)", link).group(1)
    username = re.search("twitter.com/(.*?)/status", link).group(1)
    output_dir = f"results/{id}"
    temp_dir = f"temp/{id}"

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    tweets_in_thread = get_thread_tweets(id)
    video_clips = list()
    tweet_ids = list()
    tasks = list()
    port = 9222
    for tweet in tweets_in_thread:
        tweet_ids.append(tweet.id)
        thread_item_link = f"https://twitter.com/{username}/status/{tweet.id}"
        tasks.append(asyncio.create_task(get_audio_video_from_tweet(thread_item_link, tweet.id, f"{temp_dir}", port)))
        port += 1
    
    for task in asyncio.as_completed(tasks):
        await task
    
    for tweet_id in tweet_ids:
        video_clips.append(create_video_clip(f"{temp_dir}/{tweet_id}.mp3", f"{temp_dir}/{tweet_id}.png"))
    
    final_clip = concatenate_videoclips(video_clips, "compose", bg_color=None, padding=0)
    final_clip.write_videofile(f"{output_dir}/{id}.mp4")

    shutil.rmtree("temp")
    
asyncio.run(main("https://twitter.com/MyBetaMod/status/1641987054446735360?s=20"))