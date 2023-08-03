from typing import Optional
import os
from tweety import Twitter
from tweety.types import Tweet
import preprocessing_text_ben as pp

from TTS.streamlabs_polly import StreamlabsPolly

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from flask_socketio import emit

twitter_app = Twitter("session")


class TweetManager:
    def __init__(self, id: int, app: Optional[Twitter] = twitter_app):
        self.id = id
        self.app = app

    @staticmethod
    def cleanup_tweet_text(text: str) -> str:
        """
        Cleanup tweet text
        :return: str, cleaned up text
        """
        text = text.lower()
        text = pp.remove_emails(text)
        text = pp.remove_urls(text)
        text = pp.remove_html_tags(text)
        return pp.remove_accented_chars(text)

    def screenshot_tweet(self, page: Page, output_path: str) -> bool:
        """
        Takes a screenshot of a tweet.

        :param page: Playwright page object
        :param url: URL of the tweet
        :param output_path: Path to save the screenshot
        :return: True if the screenshot was successful, False otherwise
        """
        try:
            # Twitter doesn't care about usernames
            page.goto(f"https://twitter.com/jack/status/{self.id}")
            page.wait_for_load_state("networkidle")

            views = page.locator("//div[contains(@class, 'r-1471scf')]")
            tweet = page.locator("(//article[@data-testid='tweet'])", has=views)
            banner = page.query_selector("#layers")
            thread_banner = page.query_selector(
                "//div[@id='react-root']/div[1]/div[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]"
            )

            for element in [banner, thread_banner]:
                page.evaluate(
                    'element => element.setAttribute("style", "display: none;")',
                    element,
                )

            tweet.screenshot(path=output_path)
            return True
        except PlaywrightTimeoutError:
            emit(
                "stage",
                {
                    "stage": "Error while screenshotting tweet, please reload the page and try again",
                    "done": False,
                },
            )
            return False

    def get_tweet(self) -> Tweet:
        """
        Get tweet
        :return: Tweet, tweet
        """
        return self.app.tweet_detail(f"{self.id}")

    def get_thread_tweets(self) -> list:
        """
        Get thread tweets
        :return: list, list of tweets
        """
        tweet = self.app.tweet_detail(f"{self.id}")
        if len(tweet.threads) == 0:  # type: ignore
            return [tweet]
        thread_tweets = tweet.threads  # type: ignore
        # Fix for first tweet in thread not being added
        if thread_tweets[0].id != tweet.id:
            thread_tweets.insert(0, tweet)
        return thread_tweets

    def get_audio_from_tweet(self, output: str, voice: str = "Matthew") -> str:
        """
        Get audio from tweet
        :return: str, text of the tweet
        """
        tweet = self.app.tweet_detail(f"{self.id}")
        tweet_text = self.cleanup_tweet_text(tweet.text)  # type: ignore
        engine = StreamlabsPolly()
        engine.run(tweet_text, os.path.join(output, f"{self.id}.mp3"), voice)
        return tweet_text
