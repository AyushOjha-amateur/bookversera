"""
fetch_missing_genres.py - recover genres that timed out in make_dataset.py.

Run:  python fetch_missing_genres.py

It reuses fetch_books() and GENRES from YOUR make_dataset.py (which is not
modified), retries only the genres missing from books.csv, and saves the merged
result as books_merged.csv. Nothing is overwritten. When you are happy with it:
keep a backup of books.csv, then rename books_merged.csv to books.csv.
"""

import time
from pathlib import Path

import pandas as pd

import make_dataset

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "books.csv"
OUTPUT_PATH = BASE_DIR / "books_merged.csv"
MAX_ATTEMPTS = 4
FIRST_WAIT_SECONDS = 10


def merge_missing(existing, fetch=make_dataset.fetch_books, genres=make_dataset.GENRES,
                  attempts=MAX_ATTEMPTS, wait=FIRST_WAIT_SECONDS, sleep=time.sleep):
    """Return (merged DataFrame, list of genres that still could not be fetched)."""
    present = set(existing["Genre"].dropna().astype(str))
    missing = [genre for genre in genres if genre not in present]
    new_rows, still_missing = [], []

    for genre in missing:
        books = []
        for attempt in range(1, attempts + 1):
            print(f"Fetching {genre} (attempt {attempt} of {attempts})...")
            books = fetch(genre, genres[genre])
            if books:
                break
            if attempt < attempts:
                delay = wait * 2 ** (attempt - 1)
                print(f"  No books returned. Waiting {delay}s before retrying...")
                sleep(delay)
        if books:
            new_rows.extend(books)
        else:
            still_missing.append(genre)
        sleep(1)  # be polite to the API

    if not new_rows:
        return existing, still_missing

    merged = pd.concat([existing, pd.DataFrame(new_rows)], ignore_index=True)
    merged["Title"] = merged["Title"].astype(str).str.strip()
    merged = merged.drop_duplicates(subset="Title", keep="first")  # existing books win
    merged["Year"] = pd.to_numeric(merged["Year"], errors="coerce")
    merged["Rating"] = pd.to_numeric(merged["Rating"], errors="coerce")
    return merged[list(existing.columns)], still_missing


def main():
    if not CSV_PATH.exists():
        print("books.csv not found. Run make_dataset.py first.")
        return
    existing = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    missing = [g for g in make_dataset.GENRES if g not in set(existing["Genre"].dropna())]
    if not missing:
        print("Nothing to do: every genre is already in books.csv.")
        return
    print("Missing genres:", ", ".join(missing), "\n")

    merged, still_missing = merge_missing(existing)
    if len(merged) == len(existing):
        print("\nNo new books were collected. Check your connection and try again later.")
        return

    merged.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print("\nSaved", OUTPUT_PATH.name, "-", len(merged), "books")
    print(merged["Genre"].value_counts().to_string())
    if still_missing:
        print("\nStill missing:", ", ".join(still_missing), "- run this script again later.")
    print("\nNext: back up books.csv, then rename books_merged.csv to books.csv.")


if __name__ == "__main__":
    main()
