from pathlib import Path
from urllib.parse import unquote
import pandas as pd
import re

BASE_DIR = Path(__file__).resolve().parent.parent

SHARES_FILE = BASE_DIR / "data/raw/Shares_970632177.csv"
ANALYTICS_FILE = BASE_DIR / "data/processed/post_analytics_parsed.csv"
OUTPUT_FILE = BASE_DIR / "data/processed/posts_with_analytics.csv"


def extract_post_id(url):
    if pd.isna(url):
        return None

    decoded_url = unquote(str(url))

    patterns = [
        r"urn:li:groupPost:(\d+-\d+)",
        r"urn:li:(?:share|ugcPost):(\d+)",
        r"(?:share|ugcPost|activity)-(\d+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, decoded_url)

        if match:
            return match.group(1)

    return None


# Read our existing datasets
shares = pd.read_csv(SHARES_FILE, dtype=str)
analytics = pd.read_csv(ANALYTICS_FILE, dtype={"post_id": str})

# Extract post identifiers from Shares.csv
shares["post_id"] = shares["ShareLink"].apply(extract_post_id)

# Check for duplicate identifiers before joining
duplicates = shares["post_id"].dropna().duplicated().sum()

if duplicates:
    raise ValueError(f"Found {duplicates} duplicate post IDs in Shares.csv")

if analytics["post_id"].dropna().duplicated().any():
    raise ValueError("Duplicate post IDs found in analytics data")

# Match using the post identifier
# Identify post URLs whose IDs could not be extracted
missing_ids = shares["post_id"].isna()

print("\nPosts with missing IDs:", missing_ids.sum())

if missing_ids.any():
    print("\nExamples of URLs we couldn't parse:")
    for url in shares.loc[missing_ids, "ShareLink"].head(10):
     print(url)

# Match only records with valid IDs
valid_shares = shares[shares["post_id"].notna()].copy()
invalid_shares = shares[shares["post_id"].isna()].copy()

valid_analytics = analytics[analytics["post_id"].notna()].copy()

# Ensure valid IDs are unique
if valid_shares["post_id"].duplicated().any():
    raise ValueError("Duplicate valid post IDs in Shares.csv")

if valid_analytics["post_id"].duplicated().any():
    raise ValueError("Duplicate valid post IDs in analytics")

# Match posts with valid IDs
matched = valid_shares.merge(
    valid_analytics,
    on="post_id",
    how="left",
    indicator=True,
    validate="one_to_one"
)

# Keep posts whose IDs couldn't be extracted
invalid_shares = invalid_shares.reindex(columns=matched.columns)
invalid_shares["_merge"] = "left_only"

# Combine all posts without losing records
combined = pd.concat(
    [matched, invalid_shares],
    ignore_index=True
)
# Save results
combined.to_csv(OUTPUT_FILE, index=False)

print("\nLINKEDIN POST MATCHING RESULTS")
print("-" * 40)

print("Posts in Shares.csv:", len(shares))
print("Analytics records:", len(analytics))
print("Matched posts:", (combined["_merge"] == "both").sum())
print("Posts without analytics:", (combined["_merge"] == "left_only").sum())

print("\nMatched posts:")
print(
    combined.loc[
        combined["_merge"] == "both",
        ["Date", "ShareLink", "impressions", "reactions", "comments", "saves"]
    ].to_string(index=False)
)

print("\nOutput:", OUTPUT_FILE)