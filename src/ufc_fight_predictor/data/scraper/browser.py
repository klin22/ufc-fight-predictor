#fetches pages
from playwright.sync_api import sync_playwright, TimeoutError
import logging
SECTION = 'a.b-statistics__sub-tabs-link[href$="/completed"]'
def fetch_page(url: str, selector: str):
    with sync_playwright() as playwright:
        #headless must be false to bypass browser check
        browser = playwright.chromium.launch(headless=False)

        page = browser.new_page()
        
        try:
            page.goto(
                url, 
                wait_until="domcontentloaded",
                timeout=60_000,
            )
            page.locator(selector).wait_for(timeout=15_000)
            return page.content()
        except TimeoutError:
            logging.exception("Timed out waiting for dom content to load")
            raise
        finally:
            browser.close()