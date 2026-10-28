
# ============================================================
# BOOKVERSERA - OPEN LIBRARY DATASET COLLECTOR
# ============================================================

import time
import requests
import pandas as pd

# Open Library's official search API.
API_URL = "https://openlibrary.org/search.json"

# Identify your project in API requests.
# Replace the example email with your own contact email.
HEADERS = {
    "User-Agent": "BookVersera-Class12-Project (eldenlord560@gmail.com)"
}

# Maximum requested books per category.
BOOKS_PER_GENRE = 100

# Each category creates a provisional genre label for our dataset.
GENRES = {
    "Fantasy": "subject:fantasy",
    "Mystery": "subject:mystery",
    "Romance": "subject:romance",
    "Science Fiction": "subject:science_fiction",
    "History": "subject:history",
    "Philosophy": "subject:philosophy",
    "Adventure": "subject:adventure",
    "Fiction": "subject:fiction",
}

# Request only the information needed by BookVersera.
FIELDS = (
    "key,title,author_name,first_publish_year,"
    "subject,cover_i,ratings_average"
)


def fetch_books(genre, query):
    # Request a batch of books belonging to the selected subject.
    params = {
        "q": query,
        "fields": FIELDS,
        "limit": BOOKS_PER_GENRE,
        "lang": "en",
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()
        results = response.json().get("docs", [])

    except (requests.RequestException, ValueError) as error:
        print(f"Could not fetch {genre}: {error}")
        return []

    books = []

    for item in results:
        title = item.get("title")
        authors = item.get("author_name", [])

        # Skip records without a title or author.
        if not title or not authors:
            continue

        # Subjects act as text features when descriptions are unavailable.
        subjects = item.get("subject", [])
        subjects = subjects[:12] if subjects else []

        work_key = item.get("key", "")

        # Keep the work ID for reference and the original source link.
        work_id = (
            work_key.split("/")[-1]
            if work_key.startswith("/works/")
            else ""
        )

        books.append({
            "Title": title.strip(),
            "Author": authors[0],
            "Genre": genre,
            "Year": item.get("first_publish_year"),
            "Rating": item.get("ratings_average"),
            "Description": ", ".join(subjects),
            "WorkID": work_id,
            "CoverID": item.get("cover_i"),
            "Subjects": ", ".join(subjects),
            "OpenLibraryURL": (
                f"https://openlibrary.org{work_key}"
                if work_key.startswith("/works/")
                else ""
            ),
        })

    print(f"{genre}: collected {len(books)} records")
    return books


def main():
    # Collect books from every category.
    all_books = []

    for genre, query in GENRES.items():
        all_books.extend(fetch_books(genre, query))

        # Pause between requests to avoid excessive API traffic.
        time.sleep(1)

    if not all_books:
        print("\nNo books collected. Check your internet connection.")
        return

    # Convert the collected records into a Pandas DataFrame.
    df = pd.DataFrame(all_books)

    # Remove duplicate titles.
    df["Title"] = df["Title"].astype(str).str.strip()
    df = df.drop_duplicates(subset="Title", keep="first")

    # Convert numeric fields safely.
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")

    # Save the dataset in the same folder as this script.
    df.to_csv("books.csv", index=False, encoding="utf-8-sig")

    print("\n" + "=" * 45)
    print("BOOKVERSERA DATASET CREATED")
    print("=" * 45)
    print("Total unique books:", len(df))
    print("Unique authors:", df["Author"].nunique())
    print("Genres represented:", df["Genre"].nunique())
    print("Books with ratings:", df["Rating"].notna().sum())

    print("\nBooks per genre:")
    print(df["Genre"].value_counts().to_string())

    print("\nSaved as books.csv")


if __name__ == "__main__":
    main()
