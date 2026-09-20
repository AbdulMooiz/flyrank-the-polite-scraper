from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import requests
import os
from datetime import datetime, timezone
import re
from pydantic import BaseModel, ValidationError
import json
import hashlib

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


def discover_book_links():
    """Visits catalogue pages 1-3 and collects every unique book URL."""
    all_links = []
    page_url = BASE_URL + "catalogue/page-1.html"
    page_num = 1

    while page_url and page_num <= 3:
        cache_name = f"catalogue-page-{page_num}.html"
        was_cached = os.path.exists(os.path.join(CACHE_DIR, cache_name))

        html = fetch_page(page_url, cache_name)
        soup = BeautifulSoup(html, "html.parser")

        # Every book on the page has a link inside an <h3><a href="..."> tag
        for tag in soup.select("h3 a"):
            relative_link = tag["href"]
            full_link = urljoin(page_url, relative_link)
            all_links.append(full_link)

        # Only wait if we actually hit the real site (not when reading from cache)
        if not was_cached:
            time.sleep(0.5)

        # Find the "next" button to go to the next page
        next_tag = soup.select_one("li.next a")
        if next_tag:
            page_url = urljoin(page_url, next_tag["href"])
            page_num += 1
        else:
            page_url = None

    unique_links = list(dict.fromkeys(all_links))  # removes duplicates, keeps order
    print(f"catalogue_pages={page_num} discovered={len(all_links)} unique_urls={len(unique_links)}")
    return unique_links


def extract_book(book_url, source_page):
    """Fetches one book's page and pulls out its raw details."""
    cache_name = hashlib.md5(book_url.encode()).hexdigest() + ".html"
    was_cached = os.path.exists(os.path.join(CACHE_DIR, cache_name))

    html = fetch_page(book_url, cache_name)
    soup = BeautifulSoup(html, "html.parser")

    if not was_cached:
        time.sleep(0.5)

    product = soup.select_one("div.product_main")
    title = product.select_one("h1").get_text(strip=True)
    price_text = product.select_one("p.price_color").get_text(strip=True)
    availability_text = product.select_one("p.availability").get_text(strip=True)

    # Rating is stored as a CSS class like "star-rating Three"
    rating_tag = product.select_one("p.star-rating")
    rating_text = rating_tag["class"][1] if rating_tag else None

    desc_tag = soup.select_one("#product_description ~ p")
    description = desc_tag.get_text(strip=True) if desc_tag else None

    return {
        "title": title,
        "product_url": book_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


class Book(BaseModel):
    title: str
    product_url: str
    price_gbp: float
    price_text: str
    availability_text: str
    rating_text: str | None
    description: str | None
    source_page: str
    fetched_at: str


def normalize(raw):
    """Converts raw scraped text into clean typed values."""
    price_number = float(raw["price_text"].replace("£", "").strip())
    return {
        "title": raw["title"],
        "product_url": raw["product_url"],
        "price_gbp": price_number,
        "price_text": raw["price_text"],
        "availability_text": raw["availability_text"],
        "rating_text": raw["rating_text"],
        "description": raw["description"],
        "source_page": raw["source_page"],
        "fetched_at": raw["fetched_at"],
    }


def validate_and_store(raw_records):
    """Checks every record against the schema and writes good/bad ones separately."""
    good_records = {}  # keyed by product_url so duplicates overwrite instead of piling up
    bad_records = []

    for raw in raw_records:
        try:
            clean = normalize(raw)
            book = Book(**clean)
            good_records[book.product_url] = book.model_dump()
        except (ValidationError, ValueError) as e:
            bad_records.append({"record": raw, "reason": str(e)})

    os.makedirs("output", exist_ok=True)
    with open("output/books.json", "w", encoding="utf-8") as f:
        json.dump(list(good_records.values()), f, indent=2)
    with open("output/errors.json", "w", encoding="utf-8") as f:
        json.dump(bad_records, f, indent=2)

    print(f"valid={len(good_records)} invalid={len(bad_records)}")
    return len(good_records), len(bad_records)


if __name__ == "__main__":
    links = discover_book_links()
    raw_records = [extract_book(url, BASE_URL + "catalogue/page-1.html") for url in links]
    validate_and_store(raw_records)