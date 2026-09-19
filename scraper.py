"""
Scraper for Canada.ca's static benefits category pages.

NOTE: This does NOT scrape the interactive "Benefits Finder" tool
(benefitsfinder.services.gc.ca), which is a JS-driven questionnaire
with no fixed list of results. Instead, it scrapes the static
"Benefits" landing page and its category sub-pages, which list real,
stable government programs.

Respects Canada.ca's terms by only reading public HTML pages at a
polite rate — no login, no personal data, no bypassing any access
controls.
"""

import json
import logging
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.canada.ca"
BENEFITS_INDEX_URL = f"{BASE_URL}/en/services/benefits.html"
OUTPUT_PATH = Path("data/benefits.json")
MAX_PROGRAMS = 20
REQUEST_DELAY_SECONDS = 1.5  # be polite — don't hammer the server

HEADERS = {
    "User-Agent": "Mozilla/5.0 (educational-project-scraper; contact: you@example.com)"
}


def fetch_html(url: str) -> str:
    """Fetch a page's HTML, raising on any HTTP error."""
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.text


def get_category_links(index_html: str) -> list[dict[str, str]]:
    """
    Parse the main Benefits page and return the category links
    listed under 'Services and information' (e.g. EI, Disability,
    Family, Housing...), skipping the interactive Finder tool link.
    """
    soup = BeautifulSoup(index_html, "html.parser")
    categories = []

    for heading in soup.select("h3 a, h2 a"):
        href = heading.get("href")
        text = heading.get_text(strip=True)

        if not href or not text:
            continue

        # Skip the interactive finder tool and non-benefit pages
        if "benefitsfinder" in href or "audience.html" in href:
            continue

        categories.append({
            "title": text,
            "url": urljoin(BASE_URL, href),
        })

    logger.info("Found %d candidate category links.", len(categories))
    return categories


def scrape_category_page(url: str) -> str:
    """Extract the main descriptive paragraph text from a category page."""
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    main = soup.find("main") or soup
    paragraphs = [p.get_text(strip=True) for p in main.find_all("p")]
    description = " ".join(paragraphs[:3])  # first few paragraphs only

    return description.strip()


def build_record(index: int, title: str, url: str, description: str) -> dict:
    """Assemble one record matching the schema expected by ingest.py."""
    return {
        "id": f"benefit-{index:03d}",
        "program_name": title,
        "category": "general",
        "description": description or "No description available.",
        "eligibility_summary": (
            "See the official page for detailed eligibility criteria."
        ),
        "official_url": url,
    }


def scrape_benefits(max_programs: int = MAX_PROGRAMS) -> list[dict]:
    """Run the full scrape and return a list of benefit records."""
    records = []

    try:
        index_html = fetch_html(BENEFITS_INDEX_URL)
    except requests.RequestException:
        logger.exception("Failed to fetch the benefits index page.")
        return records

    categories = get_category_links(index_html)[:max_programs]

    for i, category in enumerate(categories, start=1):
        try:
            description = scrape_category_page(category["url"])
            records.append(
                build_record(i, category["title"], category["url"], description)
            )
            logger.info("Scraped: %s", category["title"])
        except requests.RequestException:
            logger.warning("Skipping %s (fetch failed).", category["url"])
        finally:
            time.sleep(REQUEST_DELAY_SECONDS)

    return records


def save_records(records: list[dict]) -> None:
    """Write the scraped records to data/benefits.json."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info("Saved %d records to %s", len(records), OUTPUT_PATH)


if __name__ =="__main__":
    scraped = scrape_benefits()
    if scraped:
        save_records(scraped)
    else:
        logger.error("No records scraped — check the scraper logic or site structure.")