"""Render recommendation data to a static HTML page for GitHub Pages."""

import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape


DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
DATA_DIR = os.path.join(DOCS_DIR, "data")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
LOCAL_TZ = ZoneInfo("America/Detroit")


def current_local_date() -> str:
    """Return today's date in the local deployment timezone."""
    return datetime.now(LOCAL_TZ).date().isoformat()


def save_daily_data(halls: list[dict], recommendation: dict) -> str:
    """Save the day's menu data and recommendation as JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    today = current_local_date()
    data = {
        "date": today,
        "recommendation": recommendation,
        "menus": halls,
    }
    filepath = os.path.join(DATA_DIR, f"{today}.json")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    return filepath


SCORE_ORDER = {"high": 0, "medium": 1, "low": 2, "none": 3}


def sort_halls(halls: list[dict]) -> list[dict]:
    """Sort halls from high to low score."""
    return sorted(halls, key=lambda h: SCORE_ORDER.get(h.get("score", "none"), 99))


def format_inline_markdown(text: str) -> Markup:
    """Convert simple markdown emphasis to safe inline HTML."""
    escaped = escape(text)
    formatted = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", str(escaped))
    return Markup(formatted.replace("\n", "<br>\n"))


def strip_inline_markdown(text: str) -> str:
    """Remove simple markdown emphasis markers for plain-text rendering."""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text)


def render_html(recommendation: dict, scraped_halls: list[dict]) -> str:
    """Render the index.html from the Jinja2 template."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html")
    today = current_local_date()

    # Build name→url map from scraped data
    url_map = {h["name"]: h["url"] for h in scraped_halls}

    rec = dict(recommendation)
    # Ensure all scraped halls appear, even if Claude omitted them
    rec_hall_names = {h["name"] for h in rec.get("halls", [])}
    for sh in scraped_halls:
        if sh["name"] not in rec_hall_names:
            rec.setdefault("halls", []).append({
                "name": sh["name"],
                "highlights": [],
                "score": "none",
                "reasoning": "No dinner service today.",
            })
    rec["halls"] = sort_halls(rec.get("halls", []))
    rec["summary"] = format_inline_markdown(rec.get("summary", ""))
    rec["recommendation"] = strip_inline_markdown(rec.get("recommendation", ""))
    for hall in rec["halls"]:
        hall["url"] = url_map.get(hall["name"], "")
        hall["reasoning"] = format_inline_markdown(hall.get("reasoning", ""))

    html = template.render(date=today, rec=rec)
    filepath = os.path.join(DOCS_DIR, "index.html")
    with open(filepath, "w") as f:
        f.write(html)
    return filepath
