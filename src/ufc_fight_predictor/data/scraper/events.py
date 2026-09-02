from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError
import logging
#for parsing completed events on ufcstats home page
#events have date, location and name

#how is the overall application going to behave? 
#need the events page
    #fetch events page -> fetch each fight, fighter, stats, etc from each event

#let's fetch the events page first
SECTION = 'a.b-statistics__sub-tabs-link[href$="/completed"]'
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
            page.locator(SECTION).wait_for(timeout=15_000)
        except TimeoutError:
            logging.exception("Timed out waiting for dom content to load")
        html = page.content()

        browser.close()

    return html
