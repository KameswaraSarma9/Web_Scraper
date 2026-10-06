"""Reusable cleaning helpers. No scraping logic here."""
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, urlunparse

RATING_MAP = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
MISSING = {"", "n/a", "na", "none", "null", "-"}


def clean_text(value):
    """Unicode-normalize, collapse whitespace; missing values become None."""
    if value is None:
        return None
    text = unicodedata.normalize("NFKC", str(value))
    text = " ".join(text.split())
    return None if text.casefold() in MISSING else text


def to_price(value):
    """'£51.77' -> 51.77. Returns None if no number can be found."""
    text = clean_text(value)
    if text is None:
        return None
    match = re.search(r"\d+(?:[.,]\d+)?", text.replace(",", ""))
    return float(match.group()) if match else None


def to_rating(value):
    """'Three' / '3' -> 3 (int). Returns None if unrecognised."""
    text = clean_text(value)
    if text is None:
        return None
    text = text.casefold()
    if text in RATING_MAP:
        return RATING_MAP[text]
    return int(text) if text.isdigit() else None


def normalize_url(value, base=None):
    text = clean_text(value)
    if text is None:
        return None
    if base:
        text = urljoin(base, text)
    p = urlparse(text)
    return urlunparse((p.scheme.lower(), p.netloc.lower(), p.path, p.params, p.query, ""))


def clean_tags(tags):
    if not tags:
        return None
    cleaned = []
    for t in tags:
        t = clean_text(t)
        if t and t.casefold() not in cleaned:
            cleaned.append(t.casefold())
    return "|".join(cleaned) or None


def build_record(raw):
    """Raw scraped dict -> standardized record."""
    return {
        "source": clean_text(raw.get("source")),
        "source_url": normalize_url(raw.get("source_url")),
        "name_or_title": clean_text(raw.get("name_or_title")),
        "category": clean_text(raw.get("category")),
        "price": to_price(raw.get("price")),
        "rating": to_rating(raw.get("rating")),
        "author": clean_text(raw.get("author")),
        "tags": clean_tags(raw.get("tags")),
        "description": clean_text(raw.get("description")),
        "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
