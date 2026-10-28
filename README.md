# BookVersera - Streamlit interface

The AI/ML core (`bookversera.py`) and `make_dataset.py` are untouched. This interface only imports them.

## Files
- `app.py` - interface entry point (pages, navigation)
- `ui_helpers.py` - design system (CSS) and HTML components
- `bookversera_adapter.py` - safe bridge to `bookversera.py`
- `test_adapter.py` - proves the interface returns the same answers as the core
- `fetch_missing_genres.py` - retries genres that timed out in `make_dataset.py`
- `.streamlit/config.toml` - dark theme; `requirements.txt` - dependencies

Keep these next to your existing `bookversera.py`, `make_dataset.py` and `books.csv`.

## Run locally
    pip install -r requirements.txt
    python make_dataset.py            # only if books.csv does not exist yet
    python fetch_missing_genres.py    # optional: recovers genres that timed out
    python test_adapter.py            # optional: should print ALL CHECKS PASSED
    streamlit run app.py

## Deploy on Streamlit Community Cloud
1. Push every file above, including `books.csv`, to one GitHub repository (all in the repo root).
2. Filenames are case-sensitive on the server: keep `books.csv` and `bookversera.py` lowercase.
3. At share.streamlit.io choose "New app", pick the repo, and set the main file to `app.py`.
Do not run `make_dataset.py` on the server; create `books.csv` on your computer first.
