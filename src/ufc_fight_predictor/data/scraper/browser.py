#fetches pages
import logging

from playwright.sync_api import sync_playwright, TimeoutError

SECTION = 'a.b-statistics__sub-tabs-link[href$="/completed"]'
logger = logging.getLogger(__name__)
#should eventually fetch all pages for completed and uncompleted fights

def fetch_page(url: str, selector: str):
    with sync_playwright() as playwright:
        #headless must be false to bypass browser check
        browser = playwright.chromium.launch(headless=False)
        try:
            page = browser.new_page()
            
            try:
                page.goto(
                    url, 
                    wait_until="domcontentloaded",
                    timeout=60_000,
                )
            except TimeoutError:
                logger.exception("Timed out waiting for dom content to load")
                raise
            try:
                page.locator(selector).first.wait_for(timeout=15_000)
                
            except TimeoutError:
                logger.exception(f"Timed out waiting for selector: {selector}")
                raise
            
            return page.content()

        finally:
            browser.close()