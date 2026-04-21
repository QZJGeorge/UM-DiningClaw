"""Use Claude API to evaluate dining hall menus and recommend the best options."""

import json
import anthropic


SYSTEM_PROMPT = """\
You are a friendly, food-loving dining guide for University of Michigan students. \
You write like a casual food blog — warm, appetizing, and fun to read. \
You will receive today's dinner menus from multiple dining halls.

Your task:
1. Look through all the menus and find the most exciting, high-quality dishes. \
Skip chicken and pork — beyond that, use your own judgment on what's worth highlighting. \
Think interesting cuisines, premium proteins, creative preparations, standout flavors.
2. For each dining hall, highlight the dishes worth going for.
3. Recommend where to eat today with enthusiasm. Talk about the food — \
how it sounds, what makes it a good pick, flavor combos worth trying.
4. If a hall doesn't have great options today, keep it brief and positive \
("not their strongest day" rather than technical critiques).
5. If NO dining hall has anything truly exciting today, be honest about it — \
the summary should reflect that it's a quieter day for dining. \
Still list all the halls as usual, but don't oversell mediocre options.

Tone rules:
- Write like you're texting a friend about where to grab dinner, not writing a report.
- Describe food appealingly: "tender roast beef", "savory bulgogi", "fresh shrimp stir fry".
- Never use words like "lower quality", "limited", "only", or "decent". \
Frame everything through what IS good, not what's lacking.
- Keep it short and punchy — a few sentences per hall max.\
"""


def format_menus(halls: list[dict]) -> str:
    """Format scraped menu data into a readable string for the prompt."""
    lines = []
    for hall in halls:
        if not hall["meals"]:
            lines.append(f"## {hall['name']}\nNo menu available today.\n")
            continue
        lines.append(f"## {hall['name']}")
        for meal, stations in hall["meals"].items():
            lines.append(f"### {meal}")
            for station, items in stations.items():
                lines.append(f"**{station}:** {', '.join(items)}")
        lines.append("")
    return "\n".join(lines)


def get_recommendation_structured(halls: list[dict]) -> dict:
    """Get recommendation as structured JSON for the website."""
    client = anthropic.Anthropic()
    menu_text = format_menus(halls)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT
        + "\n\nRespond in JSON format with this structure:\n"
        '{"recommendation": "your main recommendation text — appetizing and friendly", '
        '"halls": [{"name": "Hall Name", "highlights": ["item1", "item2"], '
        '"score": "high/medium/low/none", '
        '"reasoning": "short, food-focused take — what makes it worth going or not"}], '
        '"summary": "one catchy line summarizing today\'s top pick"}\n'
        "IMPORTANT: Include ALL dining halls in the halls array, even those with no menu today. "
        'For halls with no menu, use score "none" and a brief friendly note like "No dinner service today". '
        "Order the halls array from best to worst — your top recommendation should be first.",
        messages=[
            {
                "role": "user",
                "content": f"Here are today's dining hall menus:\n\n{menu_text}\n\nWhich dining hall should I go to for the best high-quality meat options? Respond in JSON.",
            }
        ],
    )

    raw = message.content[0].text
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"Warning: Failed to parse Claude's response as JSON. Raw response:\n{raw}")
        raise
