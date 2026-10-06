from processing.cleaning import build_record, clean_text, normalize_url, to_price, to_rating
from processing.deduplication import dedupe
from processing.validation import validate_record


def test_clean_text():
    assert clean_text("  a   b \n") == "a b"
    assert clean_text("N/A") is None and clean_text(None) is None


def test_price_and_rating():
    assert to_price("£51.77") == 51.77
    assert to_price("free") is None
    assert to_rating("Three") == 3 and to_rating("9x") is None


def test_normalize_url():
    assert normalize_url("HTTPS://Books.ToScrape.com/a#frag") == "https://books.toscrape.com/a"


def _book(title, price="£1.00", rating="Two"):
    return build_record({"source": "Books to Scrape", "source_url": "https://books.toscrape.com/x",
                         "name_or_title": title, "price": price, "rating": rating})


def test_validation():
    assert validate_record(_book("A")) == []
    assert "book_missing_price" in validate_record(_book("A", price=None))
    assert "missing_name_or_title" in validate_record(_book("  "))


def test_dedupe_case_and_whitespace():
    recs = [_book("Example Book Title"), _book(" example   BOOK title "), _book("Other")]
    unique, dups = dedupe(recs)
    assert len(unique) == 2 and len(dups) == 1
