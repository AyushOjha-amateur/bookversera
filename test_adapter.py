"""
test_adapter.py - proves the interface gives the SAME answers as your core.

Run:  python test_adapter.py

It runs your original recommend_books() and predict_genre() (with typed input
simulated) and checks that bookversera_adapter returns identical results. It
also prints the SHA-256 fingerprint of bookversera.py: run this before and after
using the app and the value must not change.
"""

import contextlib
import hashlib
import io
import re
import sys
import warnings
from unittest import mock

import numpy as np

import bookversera_adapter as adapter
import ui_helpers

failures = []


def check(label, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + label + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failures.append(label)


def run_core_function(func, answers):
    """Run a core function that uses input(), feeding it the given answers."""
    feed = iter(answers)
    output = io.StringIO()
    with mock.patch("builtins.input", lambda *_: next(feed)), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with contextlib.redirect_stdout(output):
            func()
    return output.getvalue()


def main():
    core_path = adapter.BASE_DIR / "bookversera.py"
    digest = hashlib.sha256(core_path.read_bytes()).hexdigest()
    print("bookversera.py SHA-256:", digest, "\n")

    lib = adapter.load_library()
    core = lib.core
    total = len(core.df)
    check("core loaded and catalogue aligned with similarity matrix",
          len(lib.catalog) == total == core.similarity_matrix.shape[0])

    # 1. Recommendations: adapter vs the core's own recommend_books()
    positions = sorted({0, total // 4, total // 2, (3 * total) // 4, total - 1})
    for pos in positions:
        title = core.df.loc[pos, "Title"]
        run_core_function(core.recommend_books, [title, str(pos)])
        expected = core.last_recommendations
        got = lib.recommend(pos)
        same = (list(expected["Title"]) == list(got["Title"])
                and np.allclose(expected["Similarity"].values, got["Similarity"].values))
        check(f"recommendations match core for book #{pos}", same)

    # 2. Genre prediction: adapter vs the core's own predict_genre()
    if lib.genre_ready:
        samples = [("", "dragons, magic, quests"), ("A history of war", "empire, politics"),
                   ("Murder at midnight", "detective crime clues"), ("zzqq", "xxyy")]
        for title, description in samples:
            printed = run_core_function(core.predict_genre, [title, description])
            core_genre = re.search(r"Predicted genre: (.+)", printed).group(1).strip()
            core_top3 = re.findall(r"^(.+?): (\d+\.\d\d)%$", printed, re.M)
            got = lib.predict_genre(title, description)
            top3 = [(str(g), f"{p * 100:.2f}") for g, p in
                    zip(got["table"]["Genre"][:3], got["table"]["Probability"][:3])]
            check(f"prediction matches core for {(title or description)[:28]!r}",
                  got["genre"] == core_genre and top3 == core_top3, f"{got['genre']} vs {core_genre}")
    else:
        print("SKIP  genre model is not ready, so prediction checks are skipped")

    # 3. Charts come from the core's own plot functions
    theme = ui_helpers.chart_theme()
    for name in ("genre_pie", "genre_bar", "year_trend", "rating_hist"):
        png = lib.chart(name, theme)
        check(f"chart '{name}' draws", bool(png) and png[:8] == b"\x89PNG\r\n\x1a\n")
    check("recommendation chart draws", bool(lib.chart("rec_scores", theme, lib.recommend(0))))
    if lib.genre_ready and core.confusion is not None:
        check("confusion matrix draws", bool(lib.chart("confusion", theme)))

    # 4. Covers and links are safe to display
    with_cover = lib.catalog[lib.catalog["CoverURL"] != ""]
    check("cover URLs are well formed (no 'nan', no decimals)",
          all(re.fullmatch(r"https://covers\.openlibrary\.org/b/id/\d+-M\.jpg", u) for u in with_cover["CoverURL"]))
    check("every Open Library link starts with https://openlibrary.org/",
          all(u == "" or u.startswith("https://openlibrary.org/") for u in lib.catalog["OpenLibraryLink"]))

    # 5. The core file was not changed by anything above
    check("bookversera.py unchanged during this test",
          hashlib.sha256(core_path.read_bytes()).hexdigest() == digest)

    print("\nALL CHECKS PASSED" if not failures else f"\n{len(failures)} CHECK(S) FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
