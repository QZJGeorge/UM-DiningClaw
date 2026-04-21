"""Scrape dinner menus from U-M dining halls."""

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://dining.umich.edu/menus-locations/dining-halls/{slug}/"

DINING_HALLS = {
    "Bursley": "bursley",
    "East Quad": "east-quad",
    "Markley": "markley",
    "Mosher-Jordan": "mosher-jordan",
    "North Quad": "north-quad",
    "South Quad": "south-quad",
    "Twigs at Oxford": "twigs-at-oxford",
    "Wolverine Village": "wolverine-village-dining-hall",
}

# Meal periods we care about (case-insensitive matching)
TARGET_MEALS = {"dinner"}


def scrape_hall(name: str, slug: str) -> dict:
    """Scrape menu for a single dining hall.

    Returns:
        {
            "name": "South Quad",
            "url": "https://...",
            "meals": {
                "Dinner": {
                    "Station Name": ["Item 1", "Item 2", ...],
                    ...
                }
            }
        }
    """
    url = BASE_URL.format(slug=slug)
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    meals = {}

    # Each meal period is an <h3> containing an <a> with the meal name,
    # followed by a <div class="courses"> with stations and items.
    for h3 in soup.find_all("h3"):
        a_tag = h3.find("a")
        if not a_tag:
            continue
        meal_name = a_tag.get_text(strip=True)
        if meal_name.lower() not in TARGET_MEALS:
            continue

        # The courses div is the next sibling div after the h3
        courses_div = h3.find_next_sibling("div", class_="courses")
        if not courses_div:
            continue

        stations = {}
        # Each station is an <h4> inside a <li>, followed by <ul class="items">
        for h4 in courses_div.find_all("h4"):
            station_name = h4.get_text(strip=True)
            items_ul = h4.find_next_sibling("ul", class_="items")
            if not items_ul:
                continue

            item_names = []
            for item_li in items_ul.find_all("li", recursive=False):
                span = item_li.find("span", class_="item-name")
                if span:
                    item_names.append(span.get_text(strip=True))
            if item_names:
                stations[station_name] = item_names

        if stations:
            meals[meal_name] = stations

    return {"name": name, "url": url, "meals": meals}


def scrape_all() -> list[dict]:
    """Scrape menus from all dining halls."""
    results = []
    for name, slug in DINING_HALLS.items():
        try:
            data = scrape_hall(name, slug)
            results.append(data)
            total_items = sum(
                len(items)
                for meal in data["meals"].values()
                for items in meal.values()
            )
            print(f"  ✓ {name}: {len(data['meals'])} meal(s), {total_items} items")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            results.append({"name": name, "url": BASE_URL.format(slug=slug), "meals": {}})
    return results


if __name__ == "__main__":
    print("Scraping dining halls...")
    halls = scrape_all()
    for hall in halls:
        print(f"\n=== {hall['name']} ===")
        for meal, stations in hall["meals"].items():
            print(f"  [{meal}]")
            for station, items in stations.items():
                print(f"    {station}: {', '.join(items)}")
