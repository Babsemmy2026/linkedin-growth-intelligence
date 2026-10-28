
from pathlib import Path
from urllib.parse import unquote
import re

import pandas as pd
import psycopg
import yaml


# ==================================================
# 1. PROJECT PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SHARES_FILE = BASE_DIR / "data/raw/Shares_970632177.csv"
ANALYTICS_FILE = BASE_DIR / "data/processed/post_analytics_parsed.csv"


# ==================================================
# 2. EXTRACT POST IDENTIFIERS
# ==================================================

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


# ==================================================
# 3. READ POST INVENTORY
# ==================================================

if not SHARES_FILE.exists():
    raise FileNotFoundError(
        f"LinkedIn shares export not found: {SHARES_FILE}"
    )

shares = pd.read_csv(SHARES_FILE, dtype=str)

required_share_columns = [
    "ShareLink",
    "Date",
    "ShareCommentary",
]

missing_share_columns = [
    column
    for column in required_share_columns
    if column not in shares.columns
]

if missing_share_columns:
    raise ValueError(
        "Shares export is missing required columns: "
        f"{missing_share_columns}"
    )

details = shares["ShareLink"].apply(extract_post_details)

shares["post_id"] = details.apply(lambda x: x[0])
shares["post_type"] = details.apply(lambda x: x[1])

posts = pd.DataFrame({
    "post_id": shares["post_id"],
    "post_type": shares["post_type"],
    "post_date": pd.to_datetime(
        shares["Date"],
        errors="coerce",
        utc=True
    ),
    "post_url": shares["ShareLink"],
    "post_content": shares["ShareCommentary"],
})

if posts["post_id"].isna().any():
    raise ValueError(
        "Some posts have missing IDs. "
        "Resolve them before loading."
    )

if posts["post_id"].duplicated().any():
    raise ValueError(
        "Duplicate post IDs found in the shares export."
    )


# ==================================================
# 4. READ PRIVATE POST ANALYTICS
# ==================================================

if not ANALYTICS_FILE.exists():
    raise FileNotFoundError(
        f"Parsed analytics CSV not found: {ANALYTICS_FILE}"
    )

analytics = pd.read_csv(
    ANALYTICS_FILE,
    dtype={"post_id": str}
)

if analytics.empty:
    raise ValueError(
        "The analytics CSV contains no records. "
        "Nothing will be loaded."
    )

if "post_id" not in analytics.columns:
    raise ValueError(
        "The analytics CSV must contain a post_id column."
    )

if analytics["post_id"].isna().any():
    raise ValueError(
        "The analytics CSV contains missing post IDs."
    )

analytics["post_id"] = analytics["post_id"].astype(str)

if analytics["post_id"].duplicated().any():
    raise ValueError(
        "The analytics CSV contains duplicate post IDs. "
        "Resolve duplicates before loading."
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

missing_metrics = [
    column
    for column in metrics
    if column not in analytics.columns
]

if missing_metrics:
    raise ValueError(
        "The analytics CSV is missing metric columns: "
        f"{missing_metrics}"
    )

# Convert metrics to nullable integers.
for column in metrics:
    analytics[column] = pd.to_numeric(
        analytics[column],
        errors="coerce"
    ).astype("Int64")

# Support older CSV files without timestamp fields.
# Missing timestamps remain missing; they are never invented.
if "collected_at" not in analytics.columns:
    analytics["collected_at"] = None

if "timestamp_source" not in analytics.columns:
    analytics["timestamp_source"] = None


# ==================================================
# 5. READ DBT CONNECTION CONFIGURATION
# ==================================================

profile_path = Path.home() / ".dbt/profiles.yml"

if not profile_path.exists():
    raise FileNotFoundError(
        f"dbt profiles file not found: {profile_path}"
    )

with open(profile_path, encoding="utf-8") as file:
    profiles = yaml.safe_load(file)

profile_name = "linkedin_intelligence"

if profile_name not in profiles:
    raise ValueError(
        f"Profile '{profile_name}' not found in {profile_path}"
    )

profile = profiles[profile_name]
target = profile.get("target", "dev")

if target not in profile.get("outputs", {}):
    raise ValueError(
        f"Target '{target}' not found in profile '{profile_name}'."
    )

config = profile["outputs"][target]

required_config_keys = [
    "host",
    "dbname",
    "user",
    "pass",
]

missing_config = [
    key
    for key in required_config_keys
    if not config.get(key)
]

if missing_config:
    raise ValueError(
        f"Missing database configuration values: {missing_config}"
    )


# ==================================================
# 6. CONNECT TO NEON
# ==================================================

connection = psycopg.connect(
    host=config["host"],
    port=config.get("port", 5432),
    dbname=config["dbname"],
    user=config["user"],
    password=config["pass"],
    sslmode="require",
)


# ==================================================
# 7. CREATE TABLES AND ENSURE TIMESTAMP COLUMNS
# ==================================================

try:
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
                    profile_viewers BIGINT,
                    collected_at TIMESTAMPTZ,
                    timestamp_source TEXT
                );
            """)

            # Add the timestamp fields to an existing table
            # without deleting or rebuilding existing records.
            cursor.execute("""
                ALTER TABLE raw.linkedin_post_analytics
                ADD COLUMN IF NOT EXISTS collected_at TIMESTAMPTZ;
            """)

            cursor.execute("""
                ALTER TABLE raw.linkedin_post_analytics
                ADD COLUMN IF NOT EXISTS timestamp_source TEXT;
            """)

            # ==========================================
            # 8. INSERT OR UPDATE HISTORICAL POSTS
            # ==========================================

            for row in posts.itertuples(index=False):

                post_date = (
                    row.post_date.to_pydatetime()
                    if pd.notna(row.post_date)
                    else None
                )

                # Keep the original inventory date but store it
                # as a timezone-naive timestamp, matching the
                # existing raw.linkedin_posts table definition.
                if post_date is not None:
                    post_date = post_date.replace(tzinfo=None)

                post_content = (
                    row.post_content
                    if pd.notna(row.post_content)
                    else None
                )

                cursor.execute("""
                    INSERT INTO raw.linkedin_posts (
                        post_id,
                        post_type,
                        post_date,
                        post_url,
                        post_content
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
                    post_date,
                    row.post_url,
                    post_content,
                ))

            # ==========================================
            # 9. INSERT OR UPDATE PRIVATE ANALYTICS
            # ==========================================

            for _, row in analytics.iterrows():

                metric_values = [
                    int(row[column])
                    if pd.notna(row[column])
                    else None
                    for column in metrics
                ]

                # Only use a timestamp supplied by the collection
                # process or an existing timestamped CSV record.
                # Never substitute the current time for older data.
                collected_at = None

                if pd.notna(row["collected_at"]):
                    parsed_timestamp = pd.to_datetime(
                        row["collected_at"],
                        utc=True,
                        errors="coerce"
                    )

                    if pd.notna(parsed_timestamp):
                        collected_at = (
                            parsed_timestamp.to_pydatetime()
                        )

                timestamp_source = None

                if pd.notna(row["timestamp_source"]):
                    source_value = str(
                        row["timestamp_source"]
                    ).strip()

                    if source_value:
                        timestamp_source = source_value

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
                        profile_viewers,
                        collected_at,
                        timestamp_source
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
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
                        profile_viewers = EXCLUDED.profile_viewers,
                        collected_at = COALESCE(
                            EXCLUDED.collected_at,
                            raw.linkedin_post_analytics.collected_at
                        ),
                        timestamp_source = COALESCE(
                            EXCLUDED.timestamp_source,
                            raw.linkedin_post_analytics.timestamp_source
                        );
                """, (
                    row["post_id"],
                    None,
                    *metric_values,
                    collected_at,
                    timestamp_source,
                ))

    print("\nLINKEDIN DATA LOADED INTO NEON")
    print("--------------------------------")
    print(f"Historical posts processed: {len(posts)}")
    print(f"Analytics records processed: {len(analytics)}")
    print("Schema: raw")
    print("Tables: linkedin_posts, linkedin_post_analytics")
    print("Timestamp columns: collected_at, timestamp_source")

except Exception:
    # The connection context rolls back an unsuccessful transaction.
    raise

finally:
    connection.close()
