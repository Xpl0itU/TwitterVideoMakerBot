from tweety.bot import Twitter, Tweet
import preprocessing_text_ben as pp

from TTS.streamlabs_polly import StreamlabsPolly

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from flask_socketio import emit

app = Twitter()


class TweetManager:
    def __init__(self, id: int):
        self.id = id

    @staticmethod
    def cleanup_tweet_text(x: str) -> str:
        """
        Cleanup tweet text
        :return: str, cleaned up text
        """
        x = x.lower()
        x = pp.remove_emails(x)
        x = pp.remove_urls(x)
        x = pp.remove_html_tags(x)
        x = pp.remove_accented_chars(x)
        return x

    @staticmethod
    async def screenshot_tweet(page: Page, url: str, output_path: str) -> bool:
        """
        Takes a screenshot of a tweet.

        :param page: Playwright page object
        :param url: URL of the tweet
        :param output_path: Path to save the screenshot
        :return: True if the screenshot was successful, False otherwise
        """
        try:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")

            views = page.locator("//div[contains(@class, 'r-1471scf')]")
            tweet = page.locator("(//article[@data-testid='tweet'])", has=views)
            banner = await page.query_selector("#layers")
            thread_banner = await page.query_selector(
                "//div[@id='react-root']/div[1]/div[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]"
            )

            for element in [banner, thread_banner]:
                await page.evaluate(
                    'element => element.setAttribute("style", "display: none;")',
                    element,
                )

            await tweet.screenshot(path=output_path)
            return True
        except PlaywrightTimeoutError:
            emit(
                "stage",
                {
                    "stage": "Error while screenshotting tweet, please reload the page and try again"
                },
                broadcast=True,
            )
            return False

    def get_tweet(self) -> Tweet:
        """
        Get tweet
        :return: Tweet, tweet
        """
        return app.tweet_detail(self.id)

    def get_thread_tweets(self) -> list:
        """
        Get thread tweets
        :return: list, list of tweets
        """
        tweet = app.tweet_detail(self.id)
        if len(tweet.threads) == 0:
            return [tweet]
        thread_tweets = tweet.threads
        # Fix for first tweet in thread not being added
        if thread_tweets[0].id != tweet.id:
            thread_tweets.insert(0, tweet)
        return thread_tweets

    def get_audio_from_tweet(self, output: str) -> str:
        """
        Get audio from tweet
        :return: str, text of the tweet
        """
        tweet = app.tweet_detail(self.id)
        tweet_text = self.cleanup_tweet_text(tweet.text)
        engine = StreamlabsPolly()
        engine.run(tweet_text, f"{output}/{self.id}.mp3")
        return tweet_text

    async def get_audio_video_from_tweet(
        self, page: Page, link: str, output: str
    ) -> bool:
        """
        Get audio and video from tweet
        :return: bool, True if success, False if fail.
        """
        self.get_audio_from_tweet(output)
        return await self.screenshot_tweet(page, link, f"{output}/{self.id}.png")
