from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd
import re

BASE = Path(__file__).resolve().parent.parent
INPUT_DIR = Path.home() / "Downloads"
OUTPUT = BASE / "data/processed/html_analytics_parsed.csv"

METRICS = {
    "impressions": ["Impressions"],
    "reach": ["Members reached", "Reach"],
    "reactions": ["Reactions"],
    "comments": ["Comments"],
    "reposts": ["Reposts"],
    "saves": ["Saves"],
    "sends": ["Sends"],
    "followers_gained": ["Followers gained"],
    "profile_viewers": ["Profile viewers"],
}

def parse_number(value):
    value = value.strip().replace(",", "")

    if re.fullmatch(r"\d+", value):
        return int(value)

    return None

def extract_metric(soup, labels):
    for label in labels:
        matches = soup.find_all(
            string=lambda text: (
                text is not None
                and text.strip().lower() == label.lower()
            )
        )

        for match in matches:
            parent = match.parent

            for ancestor in list(parent.parents)[:5]:
                text = ancestor.get_text(" ", strip=True)

                if len(text) > 180:
                    continue

                escaped = re.escape(label)

                patterns = [
                    rf"^([\d,]+)\s+{escaped}$",
                    rf"^{escaped}\s+([\d,]+)$",
                ]

                for pattern in patterns:
                    result = re.search(
                        pattern,
                        text,
                        flags=re.IGNORECASE
                    )

                    if result:
                        return parse_number(result.group(1))

    return None

def extract_activity_id(soup):
    match = re.search(
        r"urn:li:activity:(\d+)",
        str(soup)
    )

    return match.group(1) if match else None

records = []

for file in sorted(INPUT_DIR.glob("linkedin_analytics*.html")):
    print("Processing:", file.name)

    soup = BeautifulSoup(
        file.read_text(encoding="utf-8", errors="replace"),
        "html.parser"
    )

    record = {
        "source_file": file.name,
        "activity_id": extract_activity_id(soup),
    }

    for metric, labels in METRICS.items():
        record[metric] = extract_metric(soup, labels)

    records.append(record)

if not records:
    print("No HTML analytics files found.")
    raise SystemExit

df = pd.DataFrame(records)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False)

print("\nEXTRACTED ANALYTICS")
print("=" * 60)
print(df.to_string(index=False))
print("\nSaved to:", OUTPUT)
