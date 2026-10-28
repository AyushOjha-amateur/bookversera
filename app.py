"""
app.py - BookVersera, a Netflix-style book discovery interface.

Run with:  streamlit run app.py

This file only builds the interface. All AI/ML work is done by your original
bookversera.py, reached through bookversera_adapter.py.
"""

import datetime
import random
import re
import traceback

import pandas as pd
import streamlit as st

import bookversera_adapter as adapter
import ui_helpers as ui

st.set_page_config(
    page_title="BookVersera", page_icon="\U0001F4D6", layout="wide",
    initial_sidebar_state="collapsed",
)

SORTS = {
    "Sort: Best match": "Best match",
    "Sort: Highest rated": "Highest rated",
    "Sort: Newest first": "Newest",
    "Sort: Oldest first": "Oldest",
}
PAGE_SIZE = 24


# ---------------------------------------------------------------------------
# Loading and small helpers
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading BookVersera's AI models...")
def get_library():
    return adapter.load_library()


def qp(name, default=""):
    value = st.query_params.get(name, default)
    return value if isinstance(value, str) else default


def qp_int(name, upper):
    try:
        value = int(qp(name))
    except ValueError:
        return None
    return value if 0 <= value < upper else None


def top_rated(frame, n=14):
    return frame.sort_values(["RatingReal", "Rating"], ascending=False).head(n)


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------
def pick_featured(catalog):
    pool = catalog[(catalog["CoverURL"] != "") & catalog["RatingReal"]]
    if pool.empty:
        pool = catalog[catalog["CoverURL"] != ""]
    if pool.empty:
        pool = catalog
    pool = pool.sort_values("Rating", ascending=False).head(12)
    rng = random.Random(datetime.date.today().toordinal())  # same pick all day
    return pool.iloc[rng.randrange(len(pool))].to_dict()


def hero_blurb(book):
    text = f"A {str(book['Genre']).lower()} title by {book['Author']}"
    year = book.get("YearInt")
    if year == year and year is not None:
        text += f", first published in {int(year)}"
    text += "."
    subjects = book.get("SubjectList") or []
    if subjects:
        text += " Open Library subjects: " + ", ".join(subjects[:5]) + "."
    return text


def build_shelves(lib):
    catalog, genres = lib.catalog, set(lib.genres)
    seed = datetime.date.today().toordinal()
    shelves = [(
        "Discover Your Next Read", "A fresh mix from across the collection, changing daily.",
        catalog.sample(n=min(14, len(catalog)), random_state=seed),
    )]

    def add(title, frame, caption=""):
        if len(frame) >= 3:
            shelves.append((title, caption, top_rated(frame)))

    add("Mystery & Suspense", catalog[catalog["Genre"] == "Mystery"])
    add("Worlds Beyond Reality", catalog[catalog["Genre"] == "Fantasy"])
    if "Romance" in genres:
        add("Stories of Love", catalog[catalog["Genre"] == "Romance"])
    else:
        loves = catalog[catalog["SubjectList"].apply(
            lambda subjects: any(re.search(r"\b(love|romance|romantic)\b", s, re.I) for s in subjects))]
        add("Stories of Love", loves, "Books whose Open Library subjects mention love or romance.")
    add("Science Fiction", catalog[catalog["Genre"] == "Science Fiction"])
    add("History & Ideas", catalog[catalog["Genre"].isin(["History", "Philosophy"])])
    add("Adventure & Journeys", catalog[catalog["Genre"] == "Adventure"])

    covered = {"Mystery", "Fantasy", "Romance", "Science Fiction", "History", "Philosophy", "Adventure"}
    for genre in lib.genres:
        if genre not in covered:
            add(genre, catalog[catalog["Genre"] == genre])

    rated = catalog[catalog["RatingReal"]]
    author_counts = catalog["Author"].value_counts()
    gems = rated[rated["Author"].map(author_counts) == 1]
    caption = "Highly rated books from authors who appear only once in this collection."
    if len(gems) < 4:
        gems, caption = rated, "The highest-rated books in the collection."
    if len(gems) >= 3:
        shelves.append(("Hidden Gems", caption, top_rated(gems)))
    return shelves


def page_home(lib):
    featured = pick_featured(lib.catalog)
    ui.render(ui.hero(featured, hero_blurb(featured)))
    for title, caption, frame in build_shelves(lib):
        ui.render(ui.shelf(title, lib.records(frame), caption))


# ---------------------------------------------------------------------------
# Discover
# ---------------------------------------------------------------------------
def page_discover(lib):
    ui.render(ui.page_top("Discover", "Search by title or author, filter by genre, or just browse the collection."))
    col_search, col_genre, col_sort = st.columns([3, 2, 2])
    query = col_search.text_input("Search books", value=qp("q"), placeholder="Search by title or author",
                                  label_visibility="collapsed")
    options = ["All genres"] + lib.genres
    start = qp("genre")
    genre = col_genre.selectbox("Genre", options, index=options.index(start) if start in options else 0,
                                label_visibility="collapsed")
    sort_label = col_sort.selectbox("Sort", list(SORTS), label_visibility="collapsed")

    results = lib.search(query, None if genre == "All genres" else genre, SORTS[sort_label])
    signature = (query, genre, sort_label)
    if st.session_state.get("_signature") != signature:
        st.session_state["_signature"] = signature
        st.session_state["_shown"] = PAGE_SIZE
    shown = st.session_state.get("_shown", PAGE_SIZE)

    total = len(results)
    if total == 0:
        detail = f' matching "{query.strip()}"' if query.strip() else ""
        where = f" in {genre}" if genre != "All genres" else ""
        ui.render(ui.empty_state(
            "No books found", f"We couldn't find any books{detail}{where}. Try a shorter search or clear the filters.",
            "Clear search and filters", ui.href("discover")))
        return

    label = "book" if total == 1 else "books"
    summary = f"{total} {label}"
    if query.strip():
        summary += f' matching "{query.strip()}"'
    if genre != "All genres":
        summary += f" in {genre}"
    ui.render(f'<p class="bv-cap">{ui.esc(summary)}. Showing {min(shown, total)}.</p>')
    ui.render(ui.grid(lib.records(results.head(shown))))
    if total > shown:
        if st.button("Show more books"):
            st.session_state["_shown"] = shown + PAGE_SIZE
            st.rerun()


# ---------------------------------------------------------------------------
# Genres
# ---------------------------------------------------------------------------
def page_genres(lib):
    catalog, chosen = lib.catalog, qp("genre")
    if chosen in lib.genres:
        frame = catalog[catalog["Genre"] == chosen].sort_values(["RatingReal", "Rating"], ascending=False)
        ui.render(ui.spacer() + ui.back_link("All genres", "genres"))
        ui.render(f'<h1 class="bv-h1">{ui.esc(chosen)}</h1><p class="bv-lede">{len(frame)} books, highest rated first.</p>')
        ui.render(ui.grid(lib.records(frame)))
        return

    ui.render(ui.page_top("Genres", "Every genre in the collection. Pick one to browse its books."))
    tiles = []
    for genre in lib.genres:
        subset = catalog[catalog["Genre"] == genre]
        covered = subset[subset["CoverURL"] != ""].sort_values("Rating", ascending=False)
        tiles.append(ui.genre_tile(genre, len(subset), covered.iloc[0]["CoverURL"] if len(covered) else ""))
    ui.render(f'<div class="bv-gtiles">{"".join(tiles)}</div>')


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
def explain(lib, source, rec):
    terms = lib.shared_terms(source["Position"], rec["Position"])
    parts = []
    if terms:
        parts.append("Shared terms: " + ", ".join(terms) + ".")
    if rec["Genre"] == source["Genre"]:
        parts.append("Same genre.")
    if rec["Author"] == source["Author"]:
        parts.append("Same author.")
    return " ".join(parts) or "Only a weak overlap in wording."


def page_recs(lib):
    ui.render(ui.page_top(
        "Recommendations",
        "Choose a book you enjoyed. BookVersera ranks every other book by how closely its title, "
        "author, genre and subjects match."))
    catalog = lib.catalog
    ordered = catalog.sort_values("Title")
    positions = [None] + [int(p) for p in ordered["Position"]]
    labels = {int(p): f"{t} - {a}" for p, t, a in zip(catalog["Position"], catalog["Title"], catalog["Author"])}

    if "rec_pick" not in st.session_state:
        st.session_state["rec_pick"] = qp_int("sim", len(catalog))

    def remember_choice():
        value = st.session_state.get("rec_pick")
        if value is None:
            if "sim" in st.query_params:
                del st.query_params["sim"]
        else:
            st.query_params["sim"] = str(value)

    pick = st.selectbox("Choose a book you like", positions, key="rec_pick", on_change=remember_choice,
                        format_func=lambda p: "Type a title or author to search..." if p is None else labels[p])

    if pick is None:
        ui.render(ui.empty_state("Pick a book to begin",
                                 "Select a book above and BookVersera will show the five most similar books in the collection."))
        sample = catalog.sample(n=min(12, len(catalog)), random_state=datetime.date.today().toordinal())
        ui.render(ui.shelf("Not sure where to start?", lib.records(sample), "Hover a book and choose Find Similar."))
        return

    with st.spinner("Finding similar books..."):
        recs = lib.recommend(pick)
        source = lib.book(pick)

    ui.render(ui.detail(source, show_similar=False))
    cards = [ui.rec_card(r, r["Similarity"], explain(lib, source, r)) for r in lib.records(recs)]
    ui.render(f'<section class="bv-shelf"><h2>Because you picked {ui.esc(source["Title"])}</h2>'
              '<p class="bv-cap">The five closest matches, with the cosine similarity score for each.</p></section>')
    ui.render(ui.rec_grid(cards))
    ui.render(
        '<div class="bv-note"><b>How this works.</b> Each book\'s title, author, genre and subject tags are turned into '
        "TF-IDF word weights. Books are then compared with cosine similarity, where 1.0 means identical wording and 0 means "
        "nothing in common. The model only sees these words, so it can't tell if two books have a similar story or tone.</div>")
    try:
        png = lib.chart("rec_scores", ui.chart_theme(), recs)
        ui.render(ui.chart_box("Similarity scores", png, "Drawn by BookVersera's own plot_recommendation_scores()."))
    except Exception:  # noqa: BLE001
        st.info("The similarity chart couldn't be drawn this time.")


# ---------------------------------------------------------------------------
# Genre prediction
# ---------------------------------------------------------------------------
def page_predict(lib):
    ui.render(ui.page_top(
        "Predict a genre",
        "Enter a title and a short description or some subjects. BookVersera's Naive Bayes model estimates the genre."))
    if not lib.genre_ready:
        ui.render(ui.empty_state(
            "The genre model isn't available",
            "It needs at least 16 books, with at least 4 in every genre. Collect more books with make_dataset.py and refresh."))
        return

    with st.form("predict_form"):
        title = st.text_input("Book title", placeholder="A title, or leave blank if you only have subjects")
        description = st.text_area("Description or subjects", height=130,
                                   placeholder="A short description, or comma-separated subjects such as: dragons, quests, magic")
        submitted = st.form_submit_button("Predict genre", type="primary")

    if not submitted:
        ui.render('<p class="bv-cap">Your estimate will appear here.</p>')
        return
    try:
        with st.spinner("Asking the model..."):
            outcome = lib.predict_genre(title, description)
    except ValueError as error:
        st.warning(str(error))
        return

    table = outcome["table"]
    best = float(table.iloc[0]["Probability"]) * 100
    ui.render(f'<div class="bv-result"><div class="k">Most likely genre</div><div class="v">{ui.esc(outcome["genre"])}</div>'
              f'<div class="k" style="margin-top:.4rem">Model confidence: {best:.1f}%</div></div>')
    if outcome["known_words"] == 0:
        st.warning("None of these words appeared in the training books, so this estimate only reflects how common each "
                   "genre is in the collection. Try adding more detail.")
    ui.render(f'<div class="bv-card-box"><h3>Probability for every genre</h3>{ui.prob_bars(table)}</div>')
    stats = lib.stats()
    ui.render(f'<div class="bv-note">These are estimates, not guaranteed classifications. The model learned from '
              f'{stats["train_size"]} books in this collection and recognised {outcome["known_words"]} word(s) in your text. '
              "Short or unusual text can give weak results.</div>")


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------
def page_insights(lib):
    stats = lib.stats()
    ui.render(ui.page_top("Insights", "Real numbers and charts from the books in this collection."))
    avg = f'{stats["avg_rating"]:.2f}' if stats["avg_rating"] is not None else "Not available"
    acc = f'{stats["accuracy"] * 100:.1f}%' if stats["accuracy"] is not None else "Not available"
    ui.render(ui.stat_tiles([
        ("Total books", f'{stats["total"]:,}'), ("Unique authors", f'{stats["authors"]:,}'),
        ("Genres", str(stats["genres"])), ("Average rating", avg), ("Genre model accuracy", acc),
    ]))

    theme = ui.chart_theme()

    def draw(name, title, note="", frame=None):
        try:
            png = lib.chart(name, theme, frame)
        except Exception:  # noqa: BLE001
            png = None
        if png:
            ui.render(ui.chart_box(title, png, note))
        else:
            st.info(f"{title}: not enough data to draw this chart.")

    with st.spinner("Drawing charts..."):
        left, right = st.columns(2)
        with left:
            draw("genre_pie", "Genre distribution")
        with right:
            draw("genre_bar", "Books per genre")
        with left:
            draw("year_trend", "Publication years")
        with right:
            draw("rating_hist", "Rating distribution",
                 f'{stats["real_ratings"]} of {stats["total"]} books have a rating on Open Library; the rest use the average.')

        sim = qp_int("sim", stats["total"])
        if sim is not None:
            draw("rec_scores", f'Similarity scores for "{lib.book(sim)["Title"]}"', frame=lib.recommend(sim))
        else:
            ui.render('<div class="bv-note">Pick a book on the <a class="bv-link" target="_self" href="'
                      + ui.esc(ui.href("recs")) + '">Recommendations</a> page and its similarity chart will appear here.</div>')

        if stats["model_ready"]:
            draw("confusion", "Genre prediction confusion matrix",
                 f'Measured on {stats["test_size"]} books the model did not train on. Rows are the real genre; columns are the prediction.')
            ui.render(f'<div class="bv-note"><b>About the {acc} accuracy.</b> Genre labels come from the search used to collect each '
                      "book, and subject tags often contain the genre word itself. That makes this collection easier than real-world "
                      "books, so expect lower accuracy on unfamiliar titles.</div>")
        else:
            ui.render('<div class="bv-note">The genre model needs at least 16 books with at least 4 per genre, so accuracy and '
                      "the confusion matrix aren't available yet.</div>")


# ---------------------------------------------------------------------------
# Book details
# ---------------------------------------------------------------------------
def page_book(lib):
    pos = qp_int("book", len(lib.catalog))
    if pos is None:
        ui.render(ui.spacer() + ui.empty_state("We couldn't find that book",
                                               "The link may be out of date. Browse the collection to find it again.",
                                               "Browse books", ui.href("discover")))
        return
    book = lib.book(pos)
    ui.render(ui.spacer() + ui.back_link() + ui.detail(book))

    similar = lib.recommend(pos, 6)
    ui.render(ui.shelf("More like this", lib.records(similar), "Ranked by TF-IDF cosine similarity."))
    catalog = lib.catalog
    same = catalog[(catalog["Author"] == book["Author"]) & (catalog["Position"] != pos)]
    if len(same):
        ui.render(ui.shelf(f"More by {book['Author']}", lib.records(same.head(14))))


PAGES = {
    "home": page_home, "discover": page_discover, "genres": page_genres,
    "recs": page_recs, "predict": page_predict, "insights": page_insights, "book": page_book,
}


def main():
    ui.inject_css()
    nav_slot = st.empty()  # filled last, so links can carry the latest choice
    page = qp("page", "home")
    page = page if page in PAGES else "home"

    try:
        lib = get_library()
    except adapter.CoreLoadError as error:
        nav_slot.markdown(ui.navbar("home"), unsafe_allow_html=True)
        ui.render(ui.spacer() + ui.empty_state("BookVersera couldn't start", str(error)))
        st.stop()
    except Exception:  # noqa: BLE001
        nav_slot.markdown(ui.navbar("home"), unsafe_allow_html=True)
        ui.render(ui.spacer() + ui.empty_state("Something went wrong while loading",
                                               "Please refresh the page. If it keeps happening, check that books.csv is valid."))
        with st.expander("Technical details"):
            st.code(traceback.format_exc())
        st.stop()

    try:
        PAGES[page](lib)
    except Exception:  # noqa: BLE001
        ui.render(ui.empty_state("This page hit a problem", "Go back to the homepage and try again.",
                                 "Back to Home", ui.href("home")))
        with st.expander("Technical details"):
            st.code(traceback.format_exc())

    ui.render(ui.footer())
    sim_now = qp_int("sim", len(lib.catalog))
    nav_slot.markdown(
        ui.navbar(page if page != "book" else "discover", qp("q") if page == "discover" else "", sim_now),
        unsafe_allow_html=True,
    )


main()
