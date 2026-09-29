#testing browser context
import logging
from playwright.sync_api import sync_playwright, BrowserContext, TimeoutError

logger = logging.getLogger(__name__)

class BrowserSession:

    def __init__(self):
        self.playwright = sync_playwright().start()
        try:
            self.browser = self.playwright.chromium.launch(headless=False)
        except Exception:
             logging.exception("Unable to open browser")
             raise
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.starting_page = "http://www.ufcstats.com/statistics/events/completed"
        try:
            self.page.goto(
                self.starting_page,
                wait_until="domcontentloaded",
                timeout=20_000,
            )
        except TimeoutError:
            logging.exception(f"Timed out visiting {self.starting_page}")
            raise

    def fetch_page(self, url: str, selector:str):
    
        try:
            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=20_000,
            )
            self.page.locator(selector).first.wait_for(timeout=15_000)
        except TimeoutError:
            logging.exception(f"Timed out visiting {url}")
            raise

        return self.page.content()
    

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    logging.info(f"Creating BrowserSession")
    browser_session = BrowserSession()