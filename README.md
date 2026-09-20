## How to run it

## 1. Clone this repo and move into the scraper folder:

git clone https://github.com/AbdulMooiz/flyrank-the-polite-scraper.git
cd yourrepo/scraper

## 2. Create a virtual environment and activate it:

python -m venv venv
venv\Scripts\Activate.ps1

## 3. Install the dependencies:

pip install requests beautifulsoup4 pydantic

## 4. Run the scraper:

python src\main.py


This produces `output/books.json` (60 validated book records), `output/errors.json` (any records that failed validation), and `output/run-report.json` (a summary of the run).

## Record schema

Each entry in `books.json` follows this shape:

| Field | Type | Notes |
|---|---|---|
| title | string | Book title |
| product_url | string | Absolute URL, used as the record's unique identity |
| price_gbp | number | Price converted to a float, e.g. 51.77 |
| price_text | string | Original price text as shown on the page, e.g. £51.77 |
| availability_text | string | Stock status as shown on the page |
| rating_text | string or null | Star rating word, e.g. Three |
| description | string or null | Book description, null when the page had none |
| source_page | string | The catalogue page this book was discovered from |
| fetched_at | string | UTC timestamp of when the page was fetched |

Records that fail this schema are written to `errors.json` along with the reason they failed, instead of being included in `books.json`.

## Politeness rules

This scraper follows a few rules so it never puts unnecessary load on the site:

- User agent: every real request identifies itself with a custom User Agent header naming this project and a link back to this repo, instead of pretending to be a browser.
- Timeout: every request gives up after 10 seconds instead of hanging indefinitely.
- Delay: the scraper waits at least half a second between real requests to the live site.
- Cache: every page fetched is saved locally in the cache folder. On later runs, or when a page has already been fetched, the saved copy is read instead of asking the site again, so repeated development runs do not hit the site repeatedly.

## Example run report

'''
{
  "start_time": "2026-09-20T20:55:48.840906+00:00",
  "duration_seconds": 7.190772,
  "pages_fetched": 61,
  "valid_records": 0,
  "invalid_records": 60,
  "failed_pages": 1
}
'''

# The Polite Scraper

## Target classification
- Site: https://books.toscrape.com
- Why: it is a public sandbox built specifically for practicing scraping
- Scope: only the first 3 catalogue pages (60 books total)
- Data collected: title, price, availability, rating, description
- robots.txt result: [paste what you saw, or write "no robots file found"]

I will not reuse this code on another site without checking its rules and terms first.