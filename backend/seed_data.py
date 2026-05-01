"""
Run this once to pre-load iPractest.com content into the vector database.
Usage: python seed_data.py
"""
from dotenv import load_dotenv
load_dotenv()

from scraper import discover_site_urls, scrape_url
from vector_store import add_documents, is_url_indexed

BASE_URL = "https://ipractest.com"


def seed():
    print(f"Discovering pages on {BASE_URL}...")
    urls = discover_site_urls(BASE_URL, max_pages=30)
    print(f"Found {len(urls)} pages.\n")

    for url in urls:
        if is_url_indexed(url):
            print(f"  [SKIP] Already indexed: {url}")
            continue

        print(f"  [SCRAPE] {url}")
        content = scrape_url(url)

        if content.startswith("ERROR:"):
            print(f"    -> {content}")
            continue

        count = add_documents([content], [{"source": url}])
        print(f"    -> Stored {count} chunks")

    print("\nSeeding complete!")


if __name__ == "__main__":
    seed()
