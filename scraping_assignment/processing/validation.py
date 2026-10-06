"""Record validation. Returns a list of error strings (empty = valid)."""
from urllib.parse import urlparse

KNOWN_SOURCES = {"Books to Scrape", "Quotes to Scrape"}


def validate_record(rec):
    errors = []
    if rec.get("source") not in KNOWN_SOURCES:
        errors.append("unknown_source")
    if not rec.get("name_or_title"):
        errors.append("missing_name_or_title")
    parsed = urlparse(rec.get("source_url") or "")
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        errors.append("invalid_url")
    price = rec.get("price")
    if price is not None and price < 0:
        errors.append("negative_price")
    rating = rec.get("rating")
    if rating is not None and not 1 <= rating <= 5:
        errors.append("rating_out_of_range")
    if rec.get("source") == "Books to Scrape":
        if price is None:
            errors.append("book_missing_price")
        if rating is None:
            errors.append("book_missing_rating")
    if rec.get("source") == "Quotes to Scrape" and not rec.get("author"):
        errors.append("quote_missing_author")
    return errors
