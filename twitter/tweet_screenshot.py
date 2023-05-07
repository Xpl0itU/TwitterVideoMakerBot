from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from flask_socketio import emit

async def screenshot_tweet(page: Page, url: str, output_path: str):
    try:
        await page.goto(url)
        await page.wait_for_load_state("networkidle")

        views = page.locator("//div[contains(@class, 'r-1471scf')]")
        tweet = page.locator("(//article[@data-testid='tweet'])", has=views)
        banner = await page.query_selector("#layers")
        thread_banner = await page.query_selector("//div[@id='react-root']/div[1]/div[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]")

        elements_to_remove = [banner, thread_banner]
        for element in elements_to_remove:
            await page.evaluate('element => element.setAttribute("style", "display: none;")', element)

        await tweet.screenshot(path=output_path)
    except PlaywrightTimeoutError:
        emit('stage', {'stage': 'Error while screenshotting tweet, please try again'}, broadcast=True)