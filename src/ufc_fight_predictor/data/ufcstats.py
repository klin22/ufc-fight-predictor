#test client
from playwright.sync_api import sync_playwright

def fetch_page(url):
    with sync_playwright() as playwright:
        #headless must be false to bypass browser check
        browser = playwright.chromium.launch(headless=False)

        page = browser.new_page()
        page.goto(
            url, 
            wait_until="domcontentloaded",
            timeout=60_0000,
        )
        page.wait_for_timeout(5_000)

        html = page.content()

        browser.close()

    return html