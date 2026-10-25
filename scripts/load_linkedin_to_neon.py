from pathlib import Path
from urllib.parse import unquote
import re

import pandas as pd
import psycopg
from dbt.config.runtime import RuntimeConfig
from dbt.task.base import get_nearest_project_dir
from dbt.cli.main import dbtRunner

BASE_DIR = Path(__file__).resolve().parent.parent

SHARES_FILE = BASE_DIR / "data/raw/Shares_970632177.csv"
ANALYTICS_FILE = BASE_DIR / "data/processed/post_analytics_parsed.csv"

# --------------------------------------------------
# 1. Extract post identifiers
# --------------------------------------------------

def extract_post_details(url):
    if pd.isna(url):
        return None, None

    decoded = unquote(str(url))

    group_match = re.search(
        r"urn:li:groupPost:(\d+-\d+)",
        decoded
    )

    if group_match:
        return group_match.group(1), "groupPost"

    regular_match = re.search(
        r"urn:li:(share|ugcPost):(\d+)",
        decoded
    )

    if regular_match:
        return regular_match.group(2), regular_match.group(1)

    match = re.search(
        r"(share|ugcPost|activity)-(\d+)",
        decoded
    )

    if match:
        return match.group(2), match.group(1)

    return None, None


# --------------------------------------------------
# 2. Read post inventory
# --------------------------------------------------

shares = pd.read_csv(SHARES_FILE, dtype=str)

details = shares["ShareLink"].apply(extract_post_details)

shares["post_id"] = details.apply(lambda x: x[0])
shares["post_type"] = details.apply(lambda x: x[1])

posts = pd.DataFrame({
    "post_id": shares["post_id"],
    "post_type": shares["post_type"],
    "post_date": pd.to_datetime(
        shares["Date"], errors="coerce"
    ),
    "post_url": shares["ShareLink"],
    "post_content": shares["ShareCommentary"],
})

if posts["post_id"].isna().any():
    raise ValueError("Some posts have missing IDs")

if posts["post_id"].duplicated().any():
    raise ValueError("Duplicate post IDs found")


# --------------------------------------------------
# 3. Read analytics
# --------------------------------------------------

analytics = pd.read_csv(
    ANALYTICS_FILE,
    dtype={"post_id": str}
)

metrics = [
    "impressions",
    "reach",
    "reactions",
    "comments",
    "reposts",
    "saves",
    "sends",
    "followers_gained",
    "profile_viewers",
]

for column in metrics:
    analytics[column] = pd.to_numeric(
        analytics[column], errors="coerce"
    ).astype("Int64")


# --------------------------------------------------
# 4. Read dbt connection configuration
# --------------------------------------------------

import yaml
import os

profile_path = Path.home() / ".dbt/profiles.yml"

with open(profile_path) as file:
    profiles = yaml.safe_load(file)

profile = profiles["linkedin_intelligence"]

target = profile.get("target", "dev")
config = profile["outputs"][target]

# --------------------------------------------------
# 5. Connect to Neon
# --------------------------------------------------

connection = psycopg.connect(
    host=config["host"],
    port=config.get("port", 5432),
    dbname=config["dbname"],
    user=config["user"],
    password=config["pass"],
    sslmode="require",
)

# --------------------------------------------------
# 6. Create tables
# --------------------------------------------------

with connection:
    with connection.cursor() as cursor:

        cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS raw;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.linkedin_posts (
                post_id TEXT PRIMARY KEY,
                post_type TEXT,
                post_date TIMESTAMP,
                post_url TEXT,
                post_content TEXT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.linkedin_post_analytics (
                post_id TEXT PRIMARY KEY,
                post_url TEXT,
                impressions BIGINT,
                reach BIGINT,
                reactions BIGINT,
                comments BIGINT,
                reposts BIGINT,
                saves BIGINT,
                sends BIGINT,
                followers_gained BIGINT,
                profile_viewers BIGINT
            );
        """)

        # ------------------------------------------
        # 7. Insert posts
        # ------------------------------------------

        for row in posts.itertuples(index=False):
            cursor.execute("""
                INSERT INTO raw.linkedin_posts (
                    post_id, post_type, post_date,
                    post_url, post_content
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (post_id)
                DO UPDATE SET
                    post_type = EXCLUDED.post_type,
                    post_date = EXCLUDED.post_date,
                    post_url = EXCLUDED.post_url,
                    post_content = EXCLUDED.post_content;
            """, (
                row.post_id,
                row.post_type,
                row.post_date.to_pydatetime()
                    if pd.notna(row.post_date) else None,
                row.post_url,
                row.post_content
                    if pd.notna(row.post_content) else None,
            ))

        # ------------------------------------------
        # 8. Insert analytics
        # ------------------------------------------

        for _, row in analytics.iterrows():

            values = [
                int(row[column])
                if pd.notna(row[column]) else None
                for column in metrics
            ]

            cursor.execute("""
                INSERT INTO raw.linkedin_post_analytics (
                    post_id,
                    post_url,
                    impressions,
                    reach,
                    reactions,
                    comments,
                    reposts,
                    saves,
                    sends,
                    followers_gained,
                    profile_viewers
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (post_id)
                DO UPDATE SET
                    post_url = EXCLUDED.post_url,
                    impressions = EXCLUDED.impressions,
                    reach = EXCLUDED.reach,
                    reactions = EXCLUDED.reactions,
                    comments = EXCLUDED.comments,
                    reposts = EXCLUDED.reposts,
                    saves = EXCLUDED.saves,
                    sends = EXCLUDED.sends,
                    followers_gained = EXCLUDED.followers_gained,
                    profile_viewers = EXCLUDED.profile_viewers;
            """, (
                row["post_id"],
                row["post_url"],
                *values,
            ))

connection.close()

print("\nLINKEDIN DATA LOADED INTO NEON")
print("--------------------------------")
print(f"Historical posts processed: {len(posts)}")
print(f"Analytics records processed: {len(analytics)}")
print("Schema: raw")
print("Tables: linkedin_posts, linkedin_post_analytics")