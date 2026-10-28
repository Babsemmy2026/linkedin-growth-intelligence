#!/usr/bin/env python3

"""
LinkedIn Growth Intelligence
Public Post Engagement Metrics Collector

Collects:
    - Reactions
    - Comments
    - Collection timestamp

Source:
    Public LinkedIn post HTML

Destination:
    Neon PostgreSQL
    raw.linkedin_post_metrics

Behavior:
    - Selects posts without existing public engagement snapshots
    - Processes all eligible posts by default
    - Supports optional --limit
    - Saves successful snapshots directly to Neon
    - Skips unavailable posts without inserting fake values
"""

import sys
import time
import argparse
import requests

from pathlib import Path
from datetime import datetime, timezone
from bs4 import BeautifulSoup

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent)
)

from classify_linkedin_media import get_database_connection


# ==========================================================
# CONFIGURATION
# ==========================================================

REQUEST_DELAY = 1

DATA_SOURCE = "linkedin_public_html"


# ==========================================================
# FETCH POSTS THAT NEED PUBLIC METRICS
# ==========================================================

def fetch_posts_for_metrics(limit=None):

    query = """
        SELECT
            p.post_id,
            p.post_url
        FROM raw.linkedin_posts AS p

        INNER JOIN raw.linkedin_post_analytics AS a
            ON p.post_id = a.post_id

        WHERE NOT EXISTS (
            SELECT 1
            FROM raw.linkedin_post_metrics AS pm
            WHERE pm.post_id = p.post_id
              AND pm.data_source = %s
        )

        ORDER BY p.post_date DESC, p.post_id DESC
    """

    params = [DATA_SOURCE]

    if limit is not None:
        query += " LIMIT %s"
        params.append(limit)

    with get_database_connection() as conn:

        with conn.cursor() as cursor:

            cursor.execute(query, tuple(params))

            rows = cursor.fetchall()

    return [
        {
            "post_id": row[0],
            "post_url": row[1]
        }
        for row in rows
    ]


# ==========================================================
# EXTRACT POST METRICS
# ==========================================================

def extract_metrics(html):

    soup = BeautifulSoup(html, "html.parser")

    article = soup.select_one(
        "article.main-feed-activity-card"
    )

    if article is None:
        return None

    reactions_element = article.select_one(
        '[data-test-id="social-actions__reactions"]'
    )

    comments_element = article.select_one(
        '[data-test-id="social-actions__comments"]'
    )

    reactions = None
    comments = None

    if reactions_element:

        value = reactions_element.get(
            "data-num-reactions"
        )

        if value is not None:
            reactions = int(value)

    if comments_element:

        value = comments_element.get(
            "data-num-comments"
        )

        if value is not None:
            comments = int(value)

    return {
        "reactions": reactions,
        "comments": comments
    }


# ==========================================================
# COLLECT METRICS
# ==========================================================

def collect_metrics(limit=None):

    print("\nLINKEDIN POST METRICS COLLECTION")
    print("=" * 60)

    posts = fetch_posts_for_metrics(limit=limit)

    print(f"Retrieved {len(posts)} unprocessed posts from Neon.\n")

    session = requests.Session()

    session.headers.update({
        "User-Agent": "Mozilla/5.0"
    })

    results = []

    for index, post in enumerate(posts, start=1):

        try:

            response = session.get(
                post["post_url"],
                timeout=20
            )

            response.raise_for_status()

            metrics = extract_metrics(response.text)

            if metrics is None:

                print(
                    f"[{index:02d}] "
                    f"{post['post_id']} | "
                    "Metrics unavailable"
                )

                continue

            if (
                metrics["reactions"] is None
                and metrics["comments"] is None
            ):

                print(
                    f"[{index:02d}] "
                    f"{post['post_id']} | "
                    "No metric values found"
                )

                continue

            results.append({
                "post_id": post["post_id"],
                "collected_at": datetime.now(timezone.utc),
                "reactions": metrics["reactions"],
                "comments": metrics["comments"],
                "data_source": DATA_SOURCE
            })

            print(
                f"[{index:02d}] "
                f"{post['post_id']} | "
                f"Reactions: {metrics['reactions']} | "
                f"Comments: {metrics['comments']}"
            )

        except (
            requests.RequestException,
            ValueError
        ) as error:

            print(
                f"[{index:02d}] "
                f"{post['post_id']} | "
                f"ERROR: {error}"
            )

        if index < len(posts):
            time.sleep(REQUEST_DELAY)

    return results


# ==========================================================
# LOAD METRICS INTO NEON
# ==========================================================

def load_metrics(results):

    if not results:
        print("\nNo metrics available to load.")
        return

    insert_sql = """
        INSERT INTO raw.linkedin_post_metrics (
            post_id,
            collected_at,
            reactions,
            comments,
            data_source
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    with get_database_connection() as conn:

        with conn.cursor() as cursor:

            for row in results:

                cursor.execute(
                    insert_sql,
                    (
                        row["post_id"],
                        row["collected_at"],
                        row["reactions"],
                        row["comments"],
                        row["data_source"]
                    )
                )

        conn.commit()

    print(
        f"\nSuccessfully loaded "
        f"{len(results)} metric snapshots into Neon."
    )


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum posts to process. Default: all eligible posts."
    )

    args = parser.parse_args()

    results = collect_metrics(limit=args.limit)

    load_metrics(results)

    print("\nCollection complete.")