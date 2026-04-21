#!/usr/bin/env python3
"""UM DiningClaw — scrape dining hall menus, get Claude's recommendation, render site."""

import os
from pathlib import Path

from scraper import scrape_all
from recommender import get_recommendation_structured
from render import save_daily_data, render_html, sort_halls


def load_local_env() -> None:
    """Populate unset environment variables from a local .env file."""
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main():
    load_local_env()

    # 1. Scrape menus
    print("Scraping dining hall menus...")
    halls = scrape_all()

    active = [h for h in halls if h["meals"]]
    print(f"\n{len(active)}/{len(halls)} halls have menus today.\n")

    if not active:
        print("No menus available today. Rendering fallback recommendation.")
        recommendation = {
            "summary": "No dinner menus are posted yet.",
            "recommendation": (
                "Michigan Dining has not posted any dinner menus yet, so there is "
                "nothing real to rank right now. Check back later once today's halls "
                "publish their menus."
            ),
            "halls": [
                {
                    "name": hall["name"],
                    "highlights": [],
                    "score": "none",
                    "reasoning": "No dinner service today.",
                }
                for hall in halls
            ],
        }
    else:
        # 2. Get Claude's recommendation
        print("Asking Claude for recommendations...")
        recommendation = get_recommendation_structured(halls)

    # 3. Print to terminal
    print(f"\n{'='*60}")
    print(f"  {recommendation['summary']}")
    print(f"{'='*60}\n")
    print(recommendation["recommendation"])
    print()
    for hall in sort_halls(recommendation.get("halls", [])):
        score = hall.get("score", "?")
        print(f"  [{score.upper()}] {hall['name']}: {hall.get('reasoning', '')}")
        if hall.get("highlights"):
            print(f"         Items: {', '.join(hall['highlights'])}")
    print()

    # 4. Save data and render HTML
    data_path = save_daily_data(halls, recommendation)
    html_path = render_html(recommendation, halls)
    print(f"Saved data:  {data_path}")
    print(f"Rendered:    {html_path}")


if __name__ == "__main__":
    main()
