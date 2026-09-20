import requests
import os

BASE_URL = "https://books.toscrape.com/"
CACHE_DIR = "cache"
HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/AbdulMooiz/flyrank-the-polite-scraper)"
}
TIMEOUT = 10  # seconds - give up if the site doesn't answer in time


def fetch_page(url, cache_filename):
    """Downloads a page, or reads it from cache if we already have it."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    # If we've already saved this page, read the saved copy instead of asking the site again
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT: {cache_filename} (size={len(html)} bytes)")
        return html

    # Otherwise, actually go fetch it from the internet
    print(f"FETCH: {url}")
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()  # stops the script if status isn't 200 (success)

    html = response.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"size={len(html)} bytes")
    return html


if __name__ == "__main__":
    fetch_page(BASE_URL + "catalogue/page-1.html", "catalogue-page-1.html")