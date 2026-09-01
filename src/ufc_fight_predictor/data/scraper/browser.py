#test client
from playwright.sync_api import sync_playwright, TimeoutError
import logging
SECTION = ".b-fight-details__person-name"
def fetch_page(url):
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
            #change this to locator
            page.wait_for_selector(
                SECTION,
                timeout=15_000
            )
        except TimeoutError:
            logging.exception(f"Timed out waiting for selector: {SECTION}")
        html = page.content()

        browser.close()

    return html