from tweety.bot import Twitter, Tweet
import preprocessing_text_ben as pp

from TTS.streamlabs_polly import StreamlabsPolly

from twitter.tweet_screenshot import screenshot_tweet
from playwright.async_api import Page

app = Twitter()


def cleanup_tweet_text(x: str) -> str:
    """
    Cleanup tweet text
    :return: str, cleaned up text
    """
    x = x.lower()
    x = pp.cont_to_exp(x)
    x = pp.remove_emails(x)
    x = pp.remove_urls(x)
    x = pp.remove_html_tags(x)
    x = pp.remove_rt(x)
    x = pp.remove_accented_chars(x)
    return x


def get_tweet(id: int) -> Tweet:
    """
    Get tweet
    :return: Tweet, tweet
    """
    return app.tweet_detail(id)


def get_thread_tweets(id: int) -> list:
    """
    Get thread tweets
    :return: list, list of tweets
    """
    tweet = app.tweet_detail(id)
    if len(tweet.threads) == 0:
        return [tweet]
    return tweet.threads


def get_audio_from_tweet(id: int, output: str) -> str:
    """
    Get audio from tweet
    :return: str, text of the tweet
    """
    tweet = app.tweet_detail(id)
    tweet_text = cleanup_tweet_text(tweet.text)
    engine = StreamlabsPolly()
    engine.run(tweet_text, f"{output}/{id}.mp3")
    return tweet_text


async def get_audio_video_from_tweet(
    page: Page, link: str, id: int, output: str
) -> bool:
    """
    Get audio and video from tweet
    :return: bool, True if success, False if fail.
    """
    get_audio_from_tweet(id, output)
    return await screenshot_tweet(page, link, f"{output}/{id}.png")