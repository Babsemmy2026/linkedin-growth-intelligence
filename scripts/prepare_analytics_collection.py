from pathlib import Path
from urllib.parse import unquote
import re
import pandas as pd

BASE = Path(__file__).resolve().parent.parent

SHARES_FILE = BASE / "data/raw/Shares_970632177.csv"
EXCEL_FILE = BASE / "data/processed/post_analytics_parsed.csv"
HTML_FILE = BASE / "data/processed/html_analytics_matched.csv"
OUTPUT_FILE = BASE / "data/processed/analytics_collection_queue.csv"
UNAVAILABLE_FILE = BASE / "data/processed/unavailable_analytics.csv"

def extract_post_id(url):
    if pd.isna(url):
        return None

    decoded = unquote(str(url))

    group = re.search(r"urn:li:groupPost:(\d+-\d+)", decoded)
    if group:
        return group.group(1)

    match = re.search(
        r"urn:li:(?:share|ugcPost|activity):(\d+)",
        decoded
    )

    if match:
        return match.group(1)

    match = re.search(
        r"(?:share|ugcPost|activity)-(\d+)",
        decoded
    )

    return match.group(1) if match else None

# Load original posts
posts = pd.read_csv(SHARES_FILE, dtype=str)
posts["post_id"] = posts["ShareLink"].apply(extract_post_id)

# Collect IDs from Excel analytics
excel_ids = set()

if EXCEL_FILE.exists():
    excel = pd.read_csv(EXCEL_FILE, dtype=str)

    # The Excel parser extracts the ORIGINAL post ID
    # from the post URL inside each report.
    excel_ids = set(
        excel["post_id"].dropna().astype(str).str.strip()
    )

    # Remove empty IDs
    excel_ids.discard("")

# Collect IDs from HTML analytics
html_ids = set()

if HTML_FILE.exists():
    html = pd.read_csv(HTML_FILE, dtype=str)
    html_ids = set(html["post_id"].dropna())

# Combine collected IDs
collected_ids = excel_ids | html_ids

# Build queue
queue = pd.DataFrame({
    "post_id": posts["post_id"],
    "post_url": posts["ShareLink"],
    "post_date": posts["Date"],
})

# Load posts confirmed unavailable.
unavailable_ids = set()
unavailable_dates = {}

if UNAVAILABLE_FILE.exists():
    unavailable = pd.read_csv(UNAVAILABLE_FILE, dtype=str)

    unavailable_ids = set(unavailable["post_id"].dropna())

    unavailable_dates = dict(
        zip(
            unavailable["post_id"],
            unavailable["checked_at"]
        )
    )

# Collected takes priority over unavailable.
def determine_status(post_id):
    if post_id in collected_ids:
        return "collected"

    if post_id in unavailable_ids:
        return "unavailable"

    return "pending"

queue["status"] = queue["post_id"].apply(determine_status)

queue["checked_at"] = queue["post_id"].map(
    unavailable_dates
)

# Validation
assert len(queue) == 638, "Unexpected number of posts"
assert queue["post_id"].notna().all(), "Missing post IDs"
assert queue["post_url"].notna().all(), "Missing URLs"
assert queue["post_id"].is_unique, "Duplicate post IDs"

# Save
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
queue.to_csv(OUTPUT_FILE, index=False)

print("\nLINKEDIN ANALYTICS COLLECTION QUEUE")
print("-" * 45)

print("Total posts:", len(queue))
print("Unique post IDs:", queue["post_id"].nunique())
print("Missing URLs:", queue["post_url"].isna().sum())
print("Duplicate IDs:", queue["post_id"].duplicated().sum())

print("\nCOLLECTION STATUS")
print("Excel analytics IDs:", len(excel_ids))
print("HTML analytics IDs:", len(html_ids))
print("Collected historical posts:", (queue["status"] == "collected").sum())
print("Pending:", (queue["status"] == "pending").sum())
print("Unavailable:", (queue["status"] == "unavailable").sum())

print("\nFIRST PENDING POST")

pending = queue[queue["status"] == "pending"]

if not pending.empty:
    print("Post ID:", pending.iloc[0]["post_id"])
    print("Post URL:", pending.iloc[0]["post_url"])
else:
    print("All posts have analytics!")

print("\nSaved to:", OUTPUT_FILE)
