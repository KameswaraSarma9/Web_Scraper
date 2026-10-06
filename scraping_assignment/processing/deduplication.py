"""Duplicate detection on normalized keys. First occurrence is kept."""
import re
import unicodedata


def normalize_key(text):
    """NFKC, casefold, punctuation -> space, collapse whitespace."""
    t = unicodedata.normalize("NFKC", text or "").casefold()
    t = re.sub(r"[^\w\s]", " ", t)
    return " ".join(t.split())


def dedupe(records):
    seen, unique, duplicates = {}, [], []
    for rec in records:
        key = (
            rec["source"],
            normalize_key(rec["name_or_title"]),
            normalize_key(rec.get("author")),
        )
        if key in seen:
            dup = dict(rec)
            dup["duplicate_of"] = seen[key]
            duplicates.append(dup)
        else:
            seen[key] = rec["source_url"]
            unique.append(rec)
    return unique, duplicates
