from tweetcapture import TweetCapture
from tweety.bot import Twitter, Tweet
import preprocessing_text_ben as pp

from TTS.streamlabs_polly import StreamlabsPolly

app = Twitter()

def cleanup_tweet_text(x: str) -> str:
    x = x.lower()
    x = pp.cont_to_exp(x)
    x = pp.remove_emails(x)
    x = pp.remove_urls(x)
    x = pp.remove_html_tags(x)
    x = pp.remove_rt(x)
    x = pp.remove_accented_chars(x)
    return x

def get_tweet(id: int) -> Tweet:
    return app.tweet_detail(id)

def get_thread_tweets(id: int) -> list:
    tweet = app.tweet_detail(id)
    if len(tweet.threads) == 0:
        return [tweet]
    return tweet.threads

async def get_audio_video_from_tweet(link: str, id: int, output: str, port: int) -> None:
    tweet = TweetCapture()
    tweet.add_chrome_argument(f"--remote-debugging-port={port}")
    await tweet.screenshot(link, f"{output}/{id}.png", mode=3, night_mode=0, overwrite=True)
    tweet = app.tweet_detail(id)
    tweet_text = cleanup_tweet_text(tweet.text)
    engine = StreamlabsPolly()
    engine.run(tweet_text, f"{output}/{id}.mp3")