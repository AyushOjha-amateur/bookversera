"""
bookversera_adapter.py
======================
Safe bridge between the Streamlit interface and your protected core file
(bookversera.py). It IMPORTS the core and reads the objects the core already
trained. It never edits, copies or retrains anything in bookversera.py.

What is reused straight from the core
-------------------------------------
  df, similarity_matrix, book_vectors, recommendation_vectorizer,
  genre_model, genre_vectorizer, genre_accuracy, confusion, X_train, X_test,
  and the core's own plot_* functions (drawn with a dark theme).

What cannot be called directly
------------------------------
recommend_books(), predict_genre() and search_books() all call input(), so
they would freeze a web app. The adapter instead reads the same trained
objects: the ranking step in Library.recommend() mirrors the core's own
(argsort on similarity_matrix, skip the chosen book, keep the top 5), and
test_adapter.py proves the results are identical to the core's.
"""

import contextlib
import importlib
import io
import os
import re
import sys
import threading
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend: safe on servers and in threads
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent
CORE_MODULE = "bookversera"
CSV_NAME = "books.csv"
COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-{size}.jpg"

REQUIRED_ATTRS = (
    "df", "similarity_matrix", "book_vectors", "recommendation_vectorizer",
    "genre_model_ready", "genre_accuracy", "confusion", "genre_model",
    "genre_vectorizer", "X_train", "X_test",
)

CHART_FUNCTIONS = {
    "genre_pie": "plot_genre_distribution",
    "genre_bar": "plot_books_by_genre",
    "year_trend": "plot_publication_trend",
    "rating_hist": "plot_rating_distribution",
    "rec_scores": "plot_recommendation_scores",
    "confusion": "plot_confusion_matrix",
}

# Open Library subject tags that describe the library catalogue, not the book.
_JUNK_SUBJECTS = {
    "accessible book", "protected daisy", "in library", "large type books",
    "internet archive wishlist", "overdrive", "lending library",
    "open library staff picks", "fiction", "general", "english",
    "english language", "english fiction", "reading level",
}
_JUNK_PREFIXES = ("nyt:", "reading level", "series:", "place:", "time:", "person:")

# Words from those catalogue tags are hidden in the "shared terms" explanation.
_JUNK_TERM_WORDS = {
    "accessible", "protected", "daisy", "library", "large", "type", "lending",
    "overdrive", "internet", "archive", "wishlist", "nyt", "reading", "level",
}

_load_lock = threading.Lock()
_plot_lock = threading.Lock()


class CoreLoadError(Exception):
    """The core file could not be loaded. The message is safe to show to users."""


# ---------------------------------------------------------------------------
# Loading the core without editing it
# ---------------------------------------------------------------------------
def load_core():
    """Import bookversera.py safely and return the module."""
    with _load_lock:
        if CORE_MODULE in sys.modules:
            return sys.modules[CORE_MODULE]

        if not (BASE_DIR / CSV_NAME).exists():
            raise CoreLoadError(
                f"{CSV_NAME} was not found next to the app. Run "
                "'python make_dataset.py' in this folder to create it, then refresh."
            )
        if not (BASE_DIR / f"{CORE_MODULE}.py").exists():
            raise CoreLoadError(f"{CORE_MODULE}.py was not found next to the app.")

        if str(BASE_DIR) not in sys.path:
            sys.path.insert(0, str(BASE_DIR))

        # The core reads "books.csv" relative to the working directory, so we
        # step into the project folder while it loads, then step back.
        previous_dir = os.getcwd()
        os.chdir(BASE_DIR)
        captured = io.StringIO()
        try:
            with contextlib.redirect_stdout(captured):
                module = importlib.import_module(CORE_MODULE)
        except SystemExit:
            # The core calls SystemExit for a missing/empty/invalid dataset.
            detail = captured.getvalue().strip().splitlines()
            raise CoreLoadError(
                "The dataset could not be used. "
                + (detail[-1] if detail else "Check that books.csv is valid.")
            )
        except Exception as error:  # noqa: BLE001
            raise CoreLoadError(f"BookVersera's core failed to load: {error}")
        finally:
            os.chdir(previous_dir)

        missing = [name for name in REQUIRED_ATTRS if not hasattr(module, name)]
        if missing:
            raise CoreLoadError(
                "bookversera.py is missing expected objects: " + ", ".join(missing)
            )
        return module


# ---------------------------------------------------------------------------
# Text helpers (display only; the model keeps using the original text)
# ---------------------------------------------------------------------------
def clean_subjects(text, limit=8):
    """Split an Open Library subject string and drop catalogue-only tags."""
    seen, result = set(), []
    for part in str(text or "").split(","):
        subject = part.strip()
        low = subject.lower()
        if not subject or low in _JUNK_SUBJECTS or low in seen:
            continue
        if low.startswith(_JUNK_PREFIXES) or len(subject) > 45:
            continue
        seen.add(low)
        result.append(subject[0].upper() + subject[1:])
        if len(result) >= limit:
            break
    return result


def _cover_urls(value):
    try:
        cover_id = int(float(value))
    except (TypeError, ValueError):
        return "", ""
    if cover_id <= 0:
        return "", ""
    return (
        COVER_URL.format(cover_id=cover_id, size="M"),
        COVER_URL.format(cover_id=cover_id, size="L"),
    )


def _safe_openlibrary_url(value):
    url = str(value or "").strip()
    return url if url.startswith("https://openlibrary.org/") else ""


# ---------------------------------------------------------------------------
# The library: one object the interface talks to
# ---------------------------------------------------------------------------
class Library:
    def __init__(self, core):
        self.core = core
        self._chart_cache = {}
        self._feature_names = None
        self.catalog = self._build_catalog()
        self.genres = sorted(self.catalog["Genre"].dropna().unique())

    # -- catalogue ---------------------------------------------------------
    def _build_catalog(self):
        df = self.core.df.copy()
        if not (df.index == np.arange(len(df))).all():
            raise CoreLoadError("The core's table is not aligned with its similarity matrix.")
        df["Position"] = np.arange(len(df))

        covers = df["CoverID"] if "CoverID" in df.columns else pd.Series([None] * len(df))
        urls = [_cover_urls(v) for v in covers]
        df["CoverURL"] = [u[0] for u in urls]
        df["CoverURLLarge"] = [u[1] for u in urls]

        links = df["OpenLibraryURL"] if "OpenLibraryURL" in df.columns else [""] * len(df)
        df["OpenLibraryLink"] = [_safe_openlibrary_url(v) for v in links]

        # The core fills missing ratings with the average. Re-read the raw CSV
        # so we can tell real ratings from filled-in ones.
        real_titles = set()
        try:
            raw = pd.read_csv(BASE_DIR / CSV_NAME, usecols=["Title", "Rating"])
            raw["Title"] = raw["Title"].astype(str).str.strip()
            raw["Rating"] = pd.to_numeric(raw["Rating"], errors="coerce")
            raw = raw.drop_duplicates(subset="Title", keep="first")
            real_titles = set(raw.loc[raw["Rating"].notna(), "Title"])
        except Exception:  # noqa: BLE001
            pass
        df["RatingReal"] = df["Title"].isin(real_titles)

        subject_col = "Subjects" if "Subjects" in df.columns else "Description"
        df["SubjectList"] = [clean_subjects(v, 12) for v in df[subject_col]]
        df["YearInt"] = pd.to_numeric(df["Year"], errors="coerce")
        return df

    def book(self, position):
        if position is None or not 0 <= int(position) < len(self.catalog):
            return None
        return self.catalog.iloc[int(position)].to_dict()

    def records(self, frame):
        return frame.to_dict("records")

    # -- search ------------------------------------------------------------
    def search(self, query="", genre=None, sort="Best match"):
        frame = self.catalog
        if genre:
            frame = frame[frame["Genre"] == genre]
        query = (query or "").strip().lower()
        if query:
            title = frame["Title"].str.lower()
            author = frame["Author"].str.lower()
            hit = title.str.contains(query, regex=False) | author.str.contains(query, regex=False)
            frame = frame[hit].copy()
            relevance = np.where(
                frame["Title"].str.lower().str.startswith(query), 0,
                np.where(frame["Title"].str.lower().str.contains(query, regex=False), 1, 2),
            )
            frame["_rel"] = relevance
        else:
            frame = frame.copy()
            frame["_rel"] = 0

        if sort == "Highest rated":
            frame = frame.sort_values(["RatingReal", "Rating", "Title"], ascending=[False, False, True])
        elif sort == "Newest":
            frame = frame.sort_values(["YearInt", "Title"], ascending=[False, True], na_position="last")
        elif sort == "Oldest":
            frame = frame.sort_values(["YearInt", "Title"], ascending=[True, True], na_position="last")
        else:
            frame = frame.sort_values(["_rel", "Title"])
        return frame.drop(columns="_rel")

    # -- recommendations (core's TF-IDF + cosine similarity) -----------------
    def recommend(self, position, n=5):
        scores = self.core.similarity_matrix[int(position)]
        ranked = np.argsort(scores)[::-1]
        picked = [int(i) for i in ranked if i != int(position)][:n]
        result = self.catalog.iloc[picked][
            ["Position", "Title", "Author", "Genre", "Rating", "RatingReal",
             "CoverURL", "CoverURLLarge", "YearInt", "SubjectList"]
        ].copy()
        result["Similarity"] = scores[picked]
        return result.reset_index(drop=True)

    def shared_terms(self, a, b, count=4):
        """Terms that contributed most to the similarity between two books."""
        if self._feature_names is None:
            self._feature_names = self.core.recommendation_vectorizer.get_feature_names_out()
        product = self.core.book_vectors[int(a)].multiply(self.core.book_vectors[int(b)]).tocoo()
        if product.nnz == 0:
            return []
        terms = []
        for i in np.argsort(product.data)[::-1]:
            term = str(self._feature_names[product.col[i]])
            # Skip fragments that straddle two fields, e.g. "12 fantasy".
            words = term.split()
            if any(w.isdigit() or w in _JUNK_TERM_WORDS for w in words):
                continue
            terms.append(term)
            if len(terms) == count:
                break
        return terms

    # -- genre prediction (core's Multinomial Naive Bayes) -------------------
    @property
    def genre_ready(self):
        return bool(self.core.genre_model_ready) and self.core.genre_model is not None

    def predict_genre(self, title, description):
        if not self.genre_ready:
            return None
        text = f"{title or ''} {description or ''}".strip()
        if not text:
            raise ValueError("Please enter a title or some description first.")
        vector = self.core.genre_vectorizer.transform([text])
        probabilities = self.core.genre_model.predict_proba(vector)[0]
        order = np.argsort(probabilities)[::-1]  # same ordering the core uses
        table = pd.DataFrame({
            "Genre": self.core.genre_model.classes_[order],
            "Probability": probabilities[order],
        })
        return {
            "genre": str(self.core.genre_model.predict(vector)[0]),
            "table": table,
            "known_words": int(vector.nnz),
        }

    # -- statistics ----------------------------------------------------------
    def stats(self):
        df = self.core.df
        rating = df["Rating"].mean() if "Rating" in df.columns else np.nan
        years = self.catalog["YearInt"].dropna()
        ready = self.genre_ready
        return {
            "total": int(len(df)),
            "authors": int(df["Author"].nunique()),
            "genres": int(df["Genre"].nunique()),
            "avg_rating": None if pd.isna(rating) else float(rating),
            "real_ratings": int(self.catalog["RatingReal"].sum()),
            "year_min": int(years.min()) if len(years) else None,
            "year_max": int(years.max()) if len(years) else None,
            "model_ready": ready,
            "accuracy": float(self.core.genre_accuracy) if ready and self.core.genre_accuracy is not None else None,
            "train_size": int(self.core.X_train.shape[0]) if ready else None,
            "test_size": int(self.core.X_test.shape[0]) if ready else None,
        }

    # -- charts: the core's own plot functions, drawn on a dark theme ----------
    def chart(self, name, rc, rec_frame=None):
        """Return PNG bytes drawn by the core's own plotting function (or None)."""
        if name not in CHART_FUNCTIONS:
            raise KeyError(name)
        cache_key = name if name != "rec_scores" else None
        if cache_key and cache_key in self._chart_cache:
            return self._chart_cache[cache_key]

        if name == "confusion" and not (self.genre_ready and self.core.confusion is not None):
            return None
        if name == "rec_scores" and (rec_frame is None or rec_frame.empty):
            return None

        with _plot_lock:
            plt.close("all")
            if name == "rec_scores":
                # The core's chart reads its module-level last_recommendations.
                self.core.last_recommendations = rec_frame[["Title", "Author", "Similarity"]].reset_index(drop=True)
            png = None
            with warnings.catch_warnings(), plt.rc_context(rc):
                warnings.simplefilter("ignore")
                with contextlib.redirect_stdout(io.StringIO()):
                    getattr(self.core, CHART_FUNCTIONS[name])()
                if plt.get_fignums():
                    figure = plt.gcf()
                    buffer = io.BytesIO()
                    figure.savefig(buffer, format="png", bbox_inches="tight",
                                   facecolor=figure.get_facecolor())
                    png = buffer.getvalue()
            plt.close("all")

        if cache_key and png:
            self._chart_cache[cache_key] = png
        return png


def load_library():
    """Load the core and wrap it. Raises CoreLoadError with a friendly message."""
    return Library(load_core())
