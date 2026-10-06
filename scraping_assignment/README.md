# Multi-Source Web Scraping & Data Consolidation

Scrapes Books to Scrape and Quotes to Scrape, cleans, validates, deduplicates and consolidates them into one dataset.

## Python version
3.9+ (developed on 3.11)

## Setup
    python -m venv venv
    source venv/bin/activate        # Windows: venv\Scripts\activate
    pip install -r requirements.txt

## Run
    python main.py                       # full run (1000 books + 100 quotes; detail pages make it take several minutes)
    python main.py --no-details          # fast: no book category/description, no author bio
    python main.py --max-pages 3         # quick test
    python -m pytest -q                  # tests
Options: `--delay`, `--output-dir`, `--log-dir`.

## Pagination
Each scraper loads page 1, then follows the `li.next a` link until none exists. No page URLs are hard-coded. `--max-pages` is a safety limit.

## Data model
`source, source_url, name_or_title, category, price, rating, author, tags, description, scraped_at`
- Books: title, price (float, GBP), rating (1-5), category and description (from product page). author/tags empty.
- Quotes: quote text as name_or_title, author, tags (pipe-separated, lowercase), description = author bio. category/price/rating empty.
- Non-applicable fields are empty (null); nothing is invented.
- Quotes have no individual URL, so source_url is the listing page the quote came from.

## Cleaning
NFKC normalization, whitespace collapse, placeholder values ("", "N/A", "none") -> null, price parsed with regex to float, rating words -> int, URLs resolved, lowercased host, fragment removed, tags lowercased and de-duplicated.

## Validation
Known source, non-empty title, valid http(s) URL, price >= 0, rating in 1-5; books must have price and rating; quotes must have an author. Rejects go to `output/rejected_records.csv` with reasons.

## Deduplication
Key = (source, normalized title/text, normalized author). Normalization: NFKC, casefold, punctuation -> space, collapse whitespace, so "Example Book Title", " Example Book Title " and "EXAMPLE BOOK TITLE" match. First occurrence is kept; removed records are written to `output/duplicates.csv` with `duplicate_of` for auditing. Source is part of the key to avoid false matches across sources.

## Error handling
Retries with exponential backoff (429/5xx), timeouts, `raise_for_status`, per-item try/except for malformed HTML, a failure in one source does not stop the other. Everything is logged to `logs/scrape.log`.

## Output
`output/final_dataset.csv`, `output/summary_report.json`, plus `rejected_records.csv`, `duplicates.csv`.

## Assumptions
Both sites are static HTML (no JS needed), so Requests + BeautifulSoup is enough. Books price is GBP.

## Known limitations
- If a listing page fails after retries, pagination for that source stops (next link unknown).
- Sequential, no checkpoint/resume.
- Exact normalized-match dedup only (no fuzzy matching).

## AI usage summary
See AI_USAGE.md.
