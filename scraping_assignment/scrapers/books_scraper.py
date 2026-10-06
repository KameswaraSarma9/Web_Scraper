"""Books to Scrape: all selectors/parsing for this source live here."""
import logging
from urllib.parse import urljoin

log = logging.getLogger(__name__)
SOURCE = "Books to Scrape"
BASE_URL = "https://books.toscrape.com/"


def _text(node):
    return node.get_text(" ", strip=True) if node else None


def _parse_card(card, page_url):
    link = card.select_one("h3 a")
    if link is None or not link.get("href"):
        raise ValueError("book card without title link")
    rating_tag = card.select_one("p.star-rating")
    rating = None
    if rating_tag:
        classes = [c for c in rating_tag.get("class", []) if c != "star-rating"]
        rating = classes[0] if classes else None
    return {
        "source": SOURCE,
        "source_url": urljoin(page_url, link["href"]),
        "name_or_title": link.get("title") or _text(link),
        "category": None,
        "price": _text(card.select_one("p.price_color")),
        "rating": rating,
        "author": None,
        "tags": None,
        "description": None,
    }


def _add_details(client, rec):
    """Category and description exist only on the product page."""
    soup = client.get_soup(rec["source_url"])
    if soup is None:
        log.warning("Detail page failed, category/description left empty: %s", rec["source_url"])
        return
    crumbs = soup.select("ul.breadcrumb li a")
    if len(crumbs) >= 3:
        rec["category"] = _text(crumbs[2])
    rec["description"] = _text(soup.select_one("#product_description ~ p"))


def scrape_books(client, max_pages=None, fetch_details=True):
    url, pages = BASE_URL, 0
    while url and (max_pages is None or pages < max_pages):
        soup = client.get_soup(url)
        if soup is None:
            log.error("Stopping Books pagination: page failed %s", url)
            break
        pages += 1
        cards = soup.select("article.product_pod")
        log.info("Books page %d: %d items (%s)", pages, len(cards), url)
        for card in cards:
            try:
                rec = _parse_card(card, url)
            except Exception as exc:  # malformed card: skip, keep going
                log.warning("Skipping malformed book card on %s: %s", url, exc)
                continue
            if fetch_details:
                _add_details(client, rec)
            yield rec
        nxt = soup.select_one("li.next a")  # pagination: follow the "next" link
        url = urljoin(url, nxt["href"]) if nxt and nxt.get("href") else None
