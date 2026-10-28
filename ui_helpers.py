"""
ui_helpers.py
=============
Design system and reusable HTML components for the BookVersera interface.

Palette:  charcoal #141414 / #1d1d1d / #262626, crimson #e50914, white, grey #a6a6a6
Type:     Fraunces (editorial serif) for titles, DM Sans for everything else.
Every piece of text that comes from the dataset is escaped before it is shown.
"""

import base64
import html
import re
from urllib.parse import urlencode

import streamlit as st

NAV_ITEMS = [
    ("home", "Home"),
    ("discover", "Discover"),
    ("genres", "Genres"),
    ("recs", "Recommendations"),
    ("predict", "Predict"),
    ("insights", "Insights"),
]


def esc(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def href(page="home", **params):
    """Build an in-app link such as ?page=book&book=12 (None values are skipped)."""
    query = {"page": page}
    query.update({k: v for k, v in params.items() if v not in (None, "")})
    return "?" + urlencode(query)


def _compact(markup):
    """Remove line breaks/indentation so Markdown never treats HTML as code."""
    return re.sub(r"\s*\n\s*", "", markup).strip()


def render(markup):
    st.markdown(_compact(markup), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Matplotlib theme used for the core's own plots
# ---------------------------------------------------------------------------
def chart_theme():
    import matplotlib
    from cycler import cycler
    from matplotlib.colors import LinearSegmentedColormap

    cmap_name = "bookversera"
    try:
        if cmap_name not in matplotlib.colormaps:
            matplotlib.colormaps.register(
                LinearSegmentedColormap.from_list(cmap_name, ["#1d1d1d", "#e50914"])
            )
    except Exception:  # noqa: BLE001
        cmap_name = "magma"
    return {
        "figure.facecolor": "#1d1d1d", "axes.facecolor": "#1d1d1d",
        "savefig.facecolor": "#1d1d1d", "axes.edgecolor": "#3a3a3a",
        "axes.labelcolor": "#d0d0d0", "text.color": "#f2f2f2",
        "axes.titlecolor": "#ffffff", "axes.titleweight": "bold",
        "xtick.color": "#b0b0b0", "ytick.color": "#b0b0b0",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "savefig.dpi": 170, "image.cmap": cmap_name,
        "axes.prop_cycle": cycler(color=[
            "#e50914", "#8e0a12", "#b8434b", "#6e6e6e",
            "#a8841f", "#4a4a4a", "#d9534f", "#7d7d7d",
        ]),
    }


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700;9..144,800&family=DM+Sans:wght@400;500;600;700&display=swap');
:root{--bg:#141414;--surface:#1d1d1d;--raised:#262626;--line:#333;--text:#fff;--muted:#a6a6a6;
--accent:#e50914;--accent-hot:#f6121d;--pad:clamp(1rem,4vw,3.5rem);--nav-h:68px;--radius:10px;
--display:'Fraunces',Georgia,'Times New Roman',serif;
--body:'DM Sans',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;}
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:var(--bg)!important;color:var(--text);font-family:var(--body);}
[data-testid="stMain"],[data-testid="stAppViewContainer"]{overflow-x:hidden;}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer{display:none!important;}
[data-testid="stMainBlockContainer"],.block-container{padding:0 var(--pad) 3rem!important;max-width:none!important;}
[data-testid="stMarkdownContainer"] a.bv-btn,[data-testid="stMarkdownContainer"] a.bv-mini,[data-testid="stMarkdownContainer"] a.bv-t,
[data-testid="stMarkdownContainer"] a.bv-link,[data-testid="stMarkdownContainer"] a.bv-logo,[data-testid="stMarkdownContainer"] a.bv-navlink,
[data-testid="stMarkdownContainer"] a.bv-gtile,[data-testid="stMarkdownContainer"] a.bv-back,[data-testid="stMarkdownContainer"] a.bv-hit{text-decoration:none!important;color:inherit;}
h1,h2,h3{font-family:var(--display);letter-spacing:-.01em;}
[data-testid="stMarkdownContainer"] .bv-h1,[data-testid="stMarkdownContainer"] .bv-hero h1,[data-testid="stMarkdownContainer"] .bv-shelf h2,[data-testid="stMarkdownContainer"] .bv-card-box h3,[data-testid="stMarkdownContainer"] .bv-empty h3{font-family:var(--display)!important;padding:0!important;}
[data-testid="stMarkdownContainer"] .bv-h1{font-size:clamp(2rem,4.2vw,3.1rem)!important;line-height:1.05!important;letter-spacing:-.025em;margin:0 0 .5rem!important;}
[data-testid="stMarkdownContainer"] .bv-hero h1{font-size:clamp(2.1rem,5.2vw,4.3rem)!important;line-height:1.05!important;}
[data-testid="stMarkdownContainer"] .bv-shelf h2{font-size:clamp(1.25rem,2.2vw,1.7rem)!important;line-height:1.2!important;margin:0!important;}
*:focus-visible{outline:2px solid #fff;outline-offset:2px;}
.bv-nav{position:fixed;top:0;left:0;right:0;z-index:1000;display:flex;align-items:center;gap:clamp(.8rem,2.4vw,2.2rem);
padding:.8rem var(--pad);background:linear-gradient(180deg,rgba(20,20,20,.97),rgba(20,20,20,.72));backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);}
.bv-logo{font:800 1.55rem/1 var(--display);letter-spacing:-.02em;color:var(--accent)!important;white-space:nowrap;}
.bv-links{display:flex;gap:clamp(.7rem,1.8vw,1.5rem);align-items:center;}
.bv-navlink{font:500 .92rem var(--body);color:#d2d2d2!important;padding:.35rem 0;border-bottom:2px solid transparent;white-space:nowrap;transition:color .15s;}
.bv-navlink:hover{color:#fff!important;}
.bv-navlink.active{color:#fff!important;border-bottom-color:var(--accent);}
.bv-search{margin-left:auto;}
.bv-search input{width:clamp(150px,22vw,270px);padding:.55rem 1rem .55rem 2.5rem;border-radius:999px;border:1px solid #3d3d3d;background:#1d1d1d
url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23a6a6a6' stroke-width='2.2' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-3.5-3.5'/%3E%3C/svg%3E") no-repeat .85rem center;
color:#fff;font:400 .9rem var(--body);transition:border-color .15s,width .2s;}
.bv-search input:focus{outline:none;border-color:var(--accent);}
.bv-top{height:calc(var(--nav-h) + 1.4rem);}
.bv-hero{position:relative;margin:0 calc(-1*var(--pad)) 1.5rem;min-height:min(80vh,660px);display:flex;align-items:flex-end;overflow:hidden;isolation:isolate;background:linear-gradient(135deg,#4a070c,#141414 70%);}
.bv-hero-bg{position:absolute;inset:-40px;background-size:cover;background-position:center 20%;filter:blur(28px) saturate(1.15) brightness(.6);z-index:-2;}
.bv-hero::after{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(90deg,rgba(20,20,20,.97) 0%,rgba(20,20,20,.8) 40%,rgba(20,20,20,.2) 100%),linear-gradient(0deg,var(--bg) 0%,rgba(20,20,20,0) 36%);}
.bv-hero-inner{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,.7fr);gap:clamp(1.5rem,5vw,4rem);align-items:center;width:100%;padding:calc(var(--nav-h) + 2.2rem) var(--pad) 3.4rem;animation:bv-in .8s ease both;}
.bv-hero h1{font:800 clamp(2.1rem,5.2vw,4.3rem)/1.05 var(--display);letter-spacing:-.025em;margin:0 0 .5rem;max-width:20ch;
display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.bv-by{font:500 1.15rem var(--body);color:#e4e4e4;margin:0;}
.bv-blurb{color:#cfcfcf;font-size:1.02rem;line-height:1.6;max-width:56ch;margin:1.3rem 0 1.6rem;}
.bv-poster{justify-self:end;width:min(100%,290px);aspect-ratio:2/3;border-radius:6px;overflow:hidden;position:relative;box-shadow:0 30px 70px rgba(0,0,0,.65);}
.bv-actions{display:flex;flex-wrap:wrap;gap:.8rem;}
.bv-btn{display:inline-flex;align-items:center;padding:.8rem 1.55rem;border-radius:6px;font:600 .98rem var(--body);cursor:pointer;transition:transform .15s,background .15s;}
.bv-btn.primary{background:var(--accent);color:#fff!important;}
.bv-btn.primary:hover{background:var(--accent-hot);transform:translateY(-1px);}
.bv-btn.ghost{background:rgba(255,255,255,.15);color:#fff!important;}
.bv-btn.ghost:hover{background:rgba(255,255,255,.26);transform:translateY(-1px);}
.bv-tags{display:flex;flex-wrap:wrap;gap:.45rem;margin:1rem 0 0;}
.bv-tag{padding:.28rem .75rem;border:1px solid rgba(255,255,255,.28);border-radius:999px;font-size:.82rem;color:#e8e8e8;background:rgba(0,0,0,.28);}
.bv-tag.genre{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600;}
.bv-shelf{margin:1.8rem 0 .6rem;}
.bv-shelf h2{font:700 clamp(1.25rem,2.2vw,1.7rem)/1.2 var(--display);margin:0;padding:0;}
.bv-cap{color:var(--muted);font-size:.88rem;margin:.2rem 0 0;}
.bv-row{display:flex;gap:1rem;overflow-x:auto;padding:1rem .6rem 1.2rem;margin:0 -.6rem;scroll-snap-type:x proximity;scrollbar-width:thin;scrollbar-color:#454545 transparent;-webkit-overflow-scrolling:touch;}
.bv-row .bv-card{flex:0 0 clamp(138px,15vw,190px);scroll-snap-align:start;}
.bv-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(clamp(138px,16vw,190px),1fr));gap:1.8rem 1.1rem;padding:.6rem 0 1rem;}
.bv-card{position:relative;transition:transform .25s cubic-bezier(.2,.7,.2,1);}
.bv-card:hover,.bv-card:focus-within{transform:scale(1.045);z-index:5;}
.bv-cover{position:relative;aspect-ratio:2/3;border-radius:var(--radius);overflow:hidden;background:var(--surface);box-shadow:0 8px 22px rgba(0,0,0,.5);}
.bv-fallback{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:space-between;padding:1rem .8rem 1rem 1.1rem;background:linear-gradient(155deg,#82090f 0%,#3a0509 75%);border-left:6px solid rgba(0,0,0,.35);}
.bv-fallback.alt{background:linear-gradient(155deg,#3d3d3d 0%,#191919 75%);}
.bv-fallback .ft{font:700 1.02rem/1.22 var(--display);color:#fff;display:-webkit-box;-webkit-line-clamp:6;-webkit-box-orient:vertical;overflow:hidden;}
.bv-fallback .fa{font-size:.76rem;color:rgba(255,255,255,.78);}
.bv-img{position:absolute;inset:0;background-size:cover;background-position:center;}
.bv-hit{position:absolute;inset:0;z-index:1;}
.bv-overlay{position:absolute;left:0;right:0;bottom:0;z-index:2;display:flex;flex-direction:column;gap:.4rem;padding:2.2rem .7rem .7rem;
background:linear-gradient(0deg,rgba(0,0,0,.94) 0%,rgba(0,0,0,.6) 60%,rgba(0,0,0,0) 100%);opacity:0;transition:opacity .2s;pointer-events:none;}
.bv-card:hover .bv-overlay,.bv-card:focus-within .bv-overlay{opacity:1;}
.bv-card:hover .bv-overlay a,.bv-card:focus-within .bv-overlay a{pointer-events:auto;}
.bv-mini{display:block;text-align:center;padding:.5rem .6rem;border-radius:5px;font:600 .82rem var(--body);background:#3a3a3a;color:#fff!important;}
.bv-mini.primary{background:var(--accent);}
.bv-mini:hover{filter:brightness(1.2);}
.bv-meta{padding:.65rem .1rem 0;}
.bv-t{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font:600 .94rem/1.25 var(--body);color:#fff!important;min-height:2.5em;}
.bv-t:hover{color:#ffb3b6!important;}
.bv-a{color:var(--muted);font-size:.82rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:.1rem;}
.bv-s{display:flex;justify-content:space-between;align-items:center;gap:.4rem;margin-top:.4rem;font-size:.76rem;color:#d0d0d0;}
.bv-s .g{border:1px solid #484848;border-radius:4px;padding:.05rem .42rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.bv-s b{color:var(--accent);}
.bv-h1{font:800 clamp(2rem,4.2vw,3.1rem)/1.05 var(--display);letter-spacing:-.025em;margin:0 0 .5rem;}
.bv-lede{color:var(--muted);max-width:62ch;line-height:1.6;margin:0 0 1.2rem;}
.bv-link{color:#fff!important;font-weight:600;border-bottom:1px solid var(--accent);}
.bv-back{display:inline-block;margin-bottom:1rem;color:var(--muted)!important;font-size:.9rem;}
.bv-back:hover{color:#fff!important;}
.bv-gtiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:1rem;margin:1rem 0 1.5rem;}
.bv-gtile{position:relative;display:flex;flex-direction:column;justify-content:flex-end;min-height:150px;padding:1.1rem;border-radius:12px;overflow:hidden;isolation:isolate;background:linear-gradient(155deg,#6d080e,#1d1d1d);transition:transform .2s;}
.bv-gtile:hover{transform:translateY(-3px);}
.bv-gtile .bg{position:absolute;inset:-20px;z-index:-2;background-size:cover;background-position:center;filter:blur(14px) brightness(.55);}
.bv-gtile::after{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(0deg,rgba(20,20,20,.88),rgba(20,20,20,.1));}
.bv-gtile .n{font:700 1.35rem var(--display);color:#fff;}
.bv-gtile .c{font-size:.85rem;color:#d0d0d0;}
.bv-detail{display:grid;grid-template-columns:minmax(150px,270px) 1fr;gap:clamp(1.2rem,4vw,3rem);align-items:start;margin:.5rem 0 1rem;}
.bv-detail .bv-poster{justify-self:start;width:100%;}
.bv-facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:.8rem;margin:1.2rem 0;max-width:520px;}
.bv-fact{background:var(--surface);border-radius:10px;padding:.7rem .9rem;}
.bv-fact .k{color:var(--muted);font-size:.78rem;}
.bv-fact .v{font:700 1.15rem var(--display);margin-top:.15rem;}
.bv-recs{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:1.4rem 1.1rem;margin:1rem 0;}
.bv-rec .bv-card:hover{transform:none;}
.bv-meter{height:6px;background:#2c2c2c;border-radius:4px;margin:.7rem 0 .3rem;overflow:hidden;}
.bv-meter i{display:block;height:100%;background:var(--accent);border-radius:4px;}
.bv-score{font-size:.82rem;color:#e0e0e0;font-weight:600;}
.bv-why{font-size:.8rem;color:var(--muted);line-height:1.5;margin-top:.25rem;}
.bv-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin:.8rem 0 1.4rem;}
.bv-stat{background:linear-gradient(180deg,#242424,#1b1b1b);border-radius:12px;padding:1.1rem 1.2rem;}
.bv-stat .v{font:800 clamp(1.7rem,3vw,2.3rem)/1.1 var(--display);}
.bv-stat .k{color:var(--muted);font-size:.85rem;margin-top:.25rem;}
.bv-card-box{background:var(--surface);border-radius:14px;padding:1.1rem 1.2rem 1.2rem;margin-bottom:1rem;}
.bv-card-box h3{font:700 1.1rem var(--display);margin:0 0 .6rem;}
.bv-card-box img{max-width:100%;max-height:560px;width:auto;height:auto;border-radius:8px;display:block;margin:0 auto;}
.bv-note{background:var(--surface);border-radius:12px;padding:1rem 1.2rem;color:#cfcfcf;font-size:.92rem;line-height:1.6;margin:.8rem 0;max-width:80ch;}
.bv-result{background:linear-gradient(135deg,#5c070d,#1d1d1d 80%);border-radius:16px;padding:1.4rem 1.6rem;margin:1rem 0;}
.bv-result .k{color:#e6c7c9;font-size:.9rem;}
.bv-result .v{font:800 clamp(1.8rem,4vw,2.7rem)/1.1 var(--display);margin-top:.2rem;}
.bv-prob{display:grid;grid-template-columns:130px 1fr 56px;gap:.8rem;align-items:center;margin:.55rem 0;font-size:.9rem;}
.bv-prob .bar{height:10px;background:#2c2c2c;border-radius:6px;overflow:hidden;}
.bv-prob .bar i{display:block;height:100%;background:#6a6a6a;border-radius:6px;}
.bv-prob.top .bar i{background:var(--accent);}
.bv-prob .p{text-align:right;color:#d0d0d0;}
.bv-empty{text-align:center;padding:3rem 1.2rem;border:1px dashed #3d3d3d;border-radius:14px;margin:1.2rem 0;}
.bv-empty h3{font:700 1.4rem var(--display);margin:0 0 .4rem;}
.bv-empty p{color:var(--muted);margin:0 auto 1.1rem;max-width:46ch;}
.bv-foot{margin-top:3rem;padding-top:1.4rem;border-top:1px solid #2a2a2a;color:#808080;font-size:.82rem;line-height:1.6;max-width:90ch;}
.bv-foot a{color:#b5b5b5!important;}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-baseweb="select"]>div{border-radius:8px!important;}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus{border-color:var(--accent)!important;box-shadow:0 0 0 1px var(--accent)!important;}
.stButton>button,[data-testid="stFormSubmitButton"]>button{border-radius:6px;font-weight:600;padding:.55rem 1.4rem;}
[data-testid="stImage"] img{border-radius:10px;}
@keyframes bv-in{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:none;}}
@media (hover:none){.bv-overlay{opacity:1;pointer-events:auto;padding-top:1.4rem;}.bv-overlay a{pointer-events:auto;}.bv-card:hover{transform:none;}}
@media (max-width:760px){
:root{--nav-h:106px;}
.bv-nav{flex-wrap:wrap;row-gap:.5rem;}
.bv-search{margin-left:auto;}
.bv-search input{width:42vw;}
.bv-links{order:3;width:100%;overflow-x:auto;gap:1.1rem;scrollbar-width:none;}
.bv-hero{min-height:auto;}
.bv-hero-inner{grid-template-columns:1fr;padding-bottom:2.4rem;}
.bv-hero .bv-poster{display:none;}
.bv-detail{grid-template-columns:1fr;}
.bv-detail .bv-poster{width:190px;}
.bv-prob{grid-template-columns:96px 1fr 48px;}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;}}
"""


def inject_css():
    st.markdown("<style>" + re.sub(r"\s*\n\s*", " ", CSS).strip() + "</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Components (each returns an HTML string)
# ---------------------------------------------------------------------------
def navbar(active, query="", sim=None):
    links = "".join(
        f'<a class="bv-navlink{" active" if key == active else ""}" target="_self" '
        f'href="{esc(href(key, sim=sim if key in ("recs", "insights") else None))}">{label}</a>'
        for key, label in NAV_ITEMS
    )
    return (
        f'<nav class="bv-nav"><a class="bv-logo" target="_self" href="{esc(href("home"))}">BookVersera</a>'
        f'<div class="bv-links">{links}</div>'
        '<form class="bv-search" method="get" action="">'
        '<input type="hidden" name="page" value="discover">'
        f'<input type="search" name="q" value="{esc(query)}" placeholder="Search title or author" aria-label="Search books">'
        "</form></nav>"
    )


def cover(book, large=False):
    url = book.get("CoverURLLarge" if large else "CoverURL") or ""
    variant = " alt" if int(book.get("Position", 0)) % 3 == 0 else ""
    fallback = (
        f'<div class="bv-fallback{variant}"><span class="ft">{esc(book.get("Title"))}</span>'
        f'<span class="fa">{esc(book.get("Author"))}</span></div>'
    )
    image = f'<div class="bv-img" style="background-image:url(\'{esc(url)}\')"></div>' if url else ""
    return fallback + image


def _rating(book):
    value = book.get("Rating")
    if book.get("RatingReal") and value == value and value is not None:
        return f'<span class="r"><b>&#9733;</b> {float(value):.1f}</span>'
    return ""


def card(book):
    pos = int(book["Position"])
    details, similar = esc(href("book", book=pos)), esc(href("recs", sim=pos))
    return (
        '<article class="bv-card">'
        f'<div class="bv-cover">{cover(book)}'
        f'<a class="bv-hit" target="_self" href="{details}" aria-label="Details for {esc(book.get("Title"))}"></a>'
        f'<div class="bv-overlay"><a class="bv-mini primary" target="_self" href="{details}">Details</a>'
        f'<a class="bv-mini" target="_self" href="{similar}">Find Similar</a></div></div>'
        f'<div class="bv-meta"><a class="bv-t" target="_self" href="{details}" title="{esc(book.get("Title"))}">{esc(book.get("Title"))}</a>'
        f'<div class="bv-a">{esc(book.get("Author"))}</div>'
        f'<div class="bv-s"><span class="g">{esc(book.get("Genre"))}</span>{_rating(book)}</div></div></article>'
    )


def shelf(title, books, caption=""):
    cap = f'<p class="bv-cap">{esc(caption)}</p>' if caption else ""
    return f'<section class="bv-shelf"><h2>{esc(title)}</h2>{cap}<div class="bv-row">{"".join(card(b) for b in books)}</div></section>'


def grid(books):
    return f'<div class="bv-grid">{"".join(card(b) for b in books)}</div>'


def hero(book, blurb):
    pos = int(book["Position"])
    bg_url = book.get("CoverURLLarge") or ""
    bg = f'<div class="bv-hero-bg" style="background-image:url(\'{esc(bg_url)}\')"></div>' if bg_url else ""
    tags = f'<span class="bv-tag genre">{esc(book.get("Genre"))}</span>' + "".join(
        f'<span class="bv-tag">{esc(s)}</span>' for s in (book.get("SubjectList") or [])[:3]
    )
    rating = f'<span class="bv-tag">&#9733; {float(book["Rating"]):.1f} on Open Library</span>' if book.get("RatingReal") else ""
    return (
        f'<section class="bv-hero">{bg}<div class="bv-hero-inner"><div>'
        f'<h1>{esc(book.get("Title"))}</h1><p class="bv-by">by {esc(book.get("Author"))}</p>'
        f'<div class="bv-tags">{tags}{rating}</div><p class="bv-blurb">{esc(blurb)}</p>'
        f'<div class="bv-actions"><a class="bv-btn primary" target="_self" href="{esc(href("book", book=pos))}">Explore Book</a>'
        f'<a class="bv-btn ghost" target="_self" href="{esc(href("recs", sim=pos))}">Find Similar Books</a></div></div>'
        f'<div class="bv-poster">{cover(book, large=True)}</div></div></section>'
    )


def page_top(title, lede=""):
    lede_html = f'<p class="bv-lede">{esc(lede)}</p>' if lede else ""
    return f'<div class="bv-top"></div><h1 class="bv-h1">{esc(title)}</h1>{lede_html}'


def spacer():
    return '<div class="bv-top"></div>'


def detail(book, show_similar=True):
    """Large book panel used on the details page and the recommendations page."""
    pos = int(book["Position"])
    tags = f'<span class="bv-tag genre">{esc(book.get("Genre"))}</span>' + "".join(
        f'<span class="bv-tag">{esc(s)}</span>' for s in (book.get("SubjectList") or [])[:8]
    )
    year = book.get("YearInt")
    year_text = str(int(year)) if year == year and year is not None else "Unknown"
    rating = f'{float(book["Rating"]):.1f} / 5' if book.get("RatingReal") else "Not rated"
    facts = fact_tiles([("First published", year_text), ("Open Library rating", rating)])
    link = book.get("OpenLibraryLink") or ""
    external = (
        f'<a class="bv-btn ghost" target="_blank" rel="noopener" href="{esc(link)}">View on Open Library</a>' if link else ""
    )
    similar_btn = (
        f'<a class="bv-btn primary" target="_self" href="{esc(href("recs", sim=pos))}">Find Similar Books</a>'
        if show_similar else ""
    )
    return (
        f'<div class="bv-detail"><div class="bv-poster">{cover(book, large=True)}</div><div>'
        f'<h1 class="bv-h1">{esc(book.get("Title"))}</h1><p class="bv-by">by {esc(book.get("Author"))}</p>'
        f'<div class="bv-tags">{tags}</div>{facts}'
        f'<div class="bv-actions">{similar_btn}{external}</div>'
        "</div></div>"
    )


def back_link(label="Back to Home", page="home"):
    return f'<a class="bv-back" target="_self" href="{esc(href(page))}">{esc(label)}</a>'


def genre_tile(genre, count, cover_url=""):
    bg = f'<div class="bg" style="background-image:url(\'{esc(cover_url)}\')"></div>' if cover_url else ""
    unit = "book" if count == 1 else "books"
    return (
        f'<a class="bv-gtile" target="_self" href="{esc(href("genres", genre=genre))}">{bg}'
        f'<span class="n">{esc(genre)}</span><span class="c">{count} {unit}</span></a>'
    )


def empty_state(title, message, link_label="", link_href=""):
    link = f'<a class="bv-btn primary" target="_self" href="{esc(link_href)}">{esc(link_label)}</a>' if link_label else ""
    return f'<div class="bv-empty"><h3>{esc(title)}</h3><p>{esc(message)}</p>{link}</div>'


def stat_tiles(items):
    tiles = "".join(f'<div class="bv-stat"><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>' for k, v in items)
    return f'<div class="bv-stats">{tiles}</div>'


def fact_tiles(items):
    tiles = "".join(f'<div class="bv-fact"><div class="k">{esc(k)}</div><div class="v">{esc(v)}</div></div>' for k, v in items)
    return f'<div class="bv-facts">{tiles}</div>'


def rec_card(book, similarity, reasons):
    width = max(0.0, min(1.0, float(similarity))) * 100
    return (
        f'<div class="bv-rec">{card(book)}<div class="bv-meter"><i style="width:{width:.1f}%"></i></div>'
        f'<div class="bv-score">Similarity {float(similarity):.3f}</div><div class="bv-why">{esc(reasons)}</div></div>'
    )


def rec_grid(cards):
    return f'<div class="bv-recs">{"".join(cards)}</div>'


def prob_bars(table, top_n=None):
    rows = []
    for i, row in enumerate(table.itertuples(index=False)):
        if top_n and i >= top_n:
            break
        pct = float(row.Probability) * 100
        rows.append(
            f'<div class="bv-prob{" top" if i == 0 else ""}"><span>{esc(row.Genre)}</span>'
            f'<span class="bar"><i style="width:{pct:.1f}%"></i></span><span class="p">{pct:.1f}%</span></div>'
        )
    return "".join(rows)


def chart_box(title, png, note=""):
    if not png:
        return ""
    data = base64.b64encode(png).decode("ascii")
    note_html = f'<p class="bv-cap" style="margin-top:.6rem">{esc(note)}</p>' if note else ""
    return f'<div class="bv-card-box"><h3>{esc(title)}</h3><img alt="{esc(title)}" src="data:image/png;base64,{data}">{note_html}</div>'


def footer():
    return (
        '<div class="bv-foot">Book data comes from <a target="_blank" rel="noopener" href="https://openlibrary.org">Open Library</a>. '
        "Recommendations use TF-IDF and cosine similarity. Genre predictions use a Multinomial Naive Bayes model. "
        "Both were built from the books in this collection only.</div>"
    )
