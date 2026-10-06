"""Pipeline: scrape -> clean -> validate -> deduplicate -> consolidate -> output."""
import argparse
import csv
import json
import logging
import time
from collections import Counter
from pathlib import Path

from processing.cleaning import build_record
from processing.deduplication import dedupe
from processing.validation import validate_record
from scrapers.books_scraper import SOURCE as BOOKS, scrape_books
from scrapers.http_client import HttpClient
from scrapers.quotes_scraper import SOURCE as QUOTES, scrape_quotes

FIELDS = ["source", "source_url", "name_or_title", "category", "price",
          "rating", "author", "tags", "description", "scraped_at"]
log = logging.getLogger("pipeline")


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def setup_logging(log_dir):
    Path(log_dir).mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(Path(log_dir) / "scrape.log", mode="w", encoding="utf-8"),
                  logging.StreamHandler()],
    )


def main():
    ap = argparse.ArgumentParser(description="Multi-source scraping pipeline")
    ap.add_argument("--max-pages", type=int, default=None, help="limit pages per source")
    ap.add_argument("--no-details", action="store_true", help="skip detail pages (faster, no category/description)")
    ap.add_argument("--delay", type=float, default=0.2, help="seconds between requests")
    ap.add_argument("--output-dir", default="output")
    ap.add_argument("--log-dir", default="logs")
    args = ap.parse_args()

    setup_logging(args.log_dir)
    out = Path(args.output_dir)
    out.mkdir(exist_ok=True)
    start = time.time()
    client = HttpClient(delay=args.delay)

    scrapers = {BOOKS: scrape_books, QUOTES: scrape_quotes}
    collected, valid, rejected = Counter(), [], []

    for name, fn in scrapers.items():
        log.info("Starting source: %s", name)
        try:
            for raw in fn(client, args.max_pages, not args.no_details):
                collected[name] += 1
                rec = build_record(raw)
                errors = validate_record(rec)
                if errors:
                    rejected.append({**rec, "errors": ";".join(errors)})
                    log.warning("Rejected %s: %s", rec.get("source_url"), errors)
                else:
                    valid.append(rec)
        except Exception:
            log.exception("Source %s aborted unexpectedly; continuing with others", name)

    final, duplicates = dedupe(valid)

    write_csv(out / "final_dataset.csv", final, FIELDS)
    write_csv(out / "rejected_records.csv", rejected, FIELDS + ["errors"])
    write_csv(out / "duplicates.csv", duplicates, FIELDS + ["duplicate_of"])

    by_source = lambda rows: dict(Counter(r["source"] for r in rows))
    summary = {
        "collected_per_source": dict(collected),
        "total_collected": sum(collected.values()),
        "total_after_cleaning_and_validation": len(valid),
        "valid_per_source": by_source(valid),
        "rejected_in_validation": len(rejected),
        "rejection_reasons": dict(Counter(e for r in rejected for e in r["errors"].split(";"))),
        "duplicates_detected_and_removed": len(duplicates),
        "final_record_count": len(final),
        "final_per_source": by_source(final),
        "execution_time_seconds": round(time.time() - start, 2),
    }
    (out / "summary_report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info("Done: %s", json.dumps(summary))


if __name__ == "__main__":
    main()
