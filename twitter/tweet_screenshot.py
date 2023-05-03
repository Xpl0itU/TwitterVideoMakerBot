from playwright.async_api import async_playwright, Playwright

async def screenshot_tweet(url: str, output_path: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector("(//article[@data-testid='tweet'])[1]")

        views = page.locator("//div[contains(@class, 'r-1471scf')]")
        tweet = page.locator("(//article[@data-testid='tweet'])", has=views)
        banner = await page.query_selector("#layers")
        thread_banner = await page.query_selector("//div[@id='react-root']/div[1]/div[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]")

        elements_to_remove = [banner, thread_banner]
        for element in elements_to_remove:
            await page.evaluate('element => element.setAttribute("style", "display: none;")', element)

        await tweet.screenshot(path=output_path)

        await browser.close()