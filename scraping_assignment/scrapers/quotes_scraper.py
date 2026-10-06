"""Quotes to Scrape: all selectors/parsing for this source live here."""
import logging
from urllib.parse import urljoin

log = logging.getLogger(__name__)
SOURCE = "Quotes to Scrape"
BASE_URL = "https://quotes.toscrape.com/"


def _text(node):
    return node.get_text(" ", strip=True) if node else None


def _author_bio(client, url, cache):
    if url in cache:
        return cache[url]
    soup = client.get_soup(url)
    bio = _text(soup.select_one(".author-description")) if soup else None
    cache[url] = bio
    return bio


def scrape_quotes(client, max_pages=None, fetch_details=True):
    url, pages, bio_cache = BASE_URL, 0, {}
    while url and (max_pages is None or pages < max_pages):
        soup = client.get_soup(url)
        if soup is None:
            log.error("Stopping Quotes pagination: page failed %s", url)
            break
        pages += 1
        blocks = soup.select("div.quote")
        log.info("Quotes page %d: %d items (%s)", pages, len(blocks), url)
        for block in blocks:
            try:
                author_link = block.select_one("a[href^='/author']")
                rec = {
                    "source": SOURCE,
                    "source_url": url,  # quotes have no individual page
                    "name_or_title": _text(block.select_one("span.text")),
                    "category": None,
                    "price": None,
                    "rating": None,
                    "author": _text(block.select_one("small.author")),
                    "tags": [t.get_text(strip=True) for t in block.select("div.tags a.tag")],
                    "description": None,
                }
                if fetch_details and author_link and author_link.get("href"):
                    rec["description"] = _author_bio(
                        client, urljoin(url, author_link["href"]), bio_cache
                    )
            except Exception as exc:
                log.warning("Skipping malformed quote on %s: %s", url, exc)
                continue
            yield rec
        nxt = soup.select_one("li.next a")
        url = urljoin(url, nxt["href"]) if nxt and nxt.get("href") else None
