from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

BASE_DOMAIN = "ipractest.com"


def _render_and_extract(page, url: str) -> str:
    page.goto(url, wait_until="networkidle", timeout=30000)

    # Scroll to trigger lazy-loaded sections
    page.evaluate("""
        async () => {
            await new Promise(resolve => {
                let total = 0;
                const distance = 400;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    total += distance;
                    if (total >= document.body.scrollHeight) {
                        clearInterval(timer);
                        resolve();
                    }
                }, 150);
            });
        }
    """)
    page.wait_for_timeout(2500)

    # Use browser's innerText — captures dynamic/rendered content including prices
    text = page.evaluate("() => document.body.innerText")
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 10]
    return "\n".join(lines)


def _get_links(page) -> list[str]:
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        links.append(a["href"])
    return links


def scrape_url(url: str) -> str:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            content = _render_and_extract(page, url)
            browser.close()
        return content
    except Exception as e:
        return f"ERROR: Could not scrape {url} — {str(e)}"


def discover_site_urls(base_url: str, max_pages: int = 30) -> list[str]:
    visited: set[str] = set()
    queue = [base_url]
    found: list[str] = []
    domain = urlparse(base_url).netloc

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            while queue and len(found) < max_pages:
                url = queue.pop(0)
                if url in visited:
                    continue
                visited.add(url)

                try:
                    page = browser.new_page()
                    _render_and_extract(page, url)
                    hrefs = _get_links(page)
                    page.close()

                    found.append(url)

                    for href in hrefs:
                        full = urljoin(url, href)
                        parsed = urlparse(full)
                        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        if parsed.netloc == domain and clean not in visited:
                            queue.append(clean)
                except Exception:
                    pass

            browser.close()
    except Exception as e:
        print(f"Discovery error: {e}")

    return found
