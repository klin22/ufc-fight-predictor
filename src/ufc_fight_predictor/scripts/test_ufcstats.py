from ufc_fight_predictor.data.ufcstats import fetch_page


test_url = "http://www.ufcstats.com/fighter-details/f689bd7bbd14b392"

html = fetch_page(test_url)
html = html.lower()

if "checking your browser" in html:
    print("FAIL: Did not pass browser javascript check")
else:
    print("SUCCESS: You have accessed the ufcstats html")
    print(html[:1000])