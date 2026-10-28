#!/usr/bin/env python3

"""
LinkedIn Growth Intelligence
Automated LinkedIn Media Format Classifier

Source:
    Neon PostgreSQL
    raw.linkedin_posts

Database connection:
    Existing dbt profile: linkedin_intelligence

Scope:
    20 most recent LinkedIn posts

Output:
    data/processed/linkedin_media_first20.csv

This script does not modify Neon PostgreSQL.
"""

import os
import re
import csv
import time
import argparse
from pathlib import Path

import yaml
import psycopg
import requests

from bs4 import BeautifulSoup
from urllib.parse import urlparse


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "linkedin_media_first20.csv"

DBT_PROFILE_NAME = "linkedin_intelligence"

DBT_PROFILE_PATH = Path.home() / ".dbt" / "profiles.yml"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def resolve_env(value):
    """
    Resolve simple dbt environment variable expressions.

    Example:
        {{ env_var('NEON_HOST') }}
    """

    if not isinstance(value, str):
        return value

    pattern = (
        r"""\{\{\s*env_var\(\s*['"]([^'"]+)['"]\s*\)\s*\}\}"""
    )

    match = re.fullmatch(pattern, value.strip())

    if match:
        variable_name = match.group(1)

        resolved_value = os.getenv(variable_name)

        if resolved_value is None:
            raise RuntimeError(
                f"Missing environment variable: {variable_name}"
            )

        return resolved_value

    return value


def get_database_connection():

    if not DBT_PROFILE_PATH.exists():
        raise FileNotFoundError(
            f"dbt profile not found: {DBT_PROFILE_PATH}"
        )

    with open(DBT_PROFILE_PATH, "r", encoding="utf-8") as file:
        profiles = yaml.safe_load(file)

    if DBT_PROFILE_NAME not in profiles:
        raise KeyError(
            f"Profile '{DBT_PROFILE_NAME}' not found in profiles.yml"
        )

    profile = profiles[DBT_PROFILE_NAME]

    target_name = profile.get("target", "dev")

    db_config = profile["outputs"][target_name]

    connection_config = {
        "host": resolve_env(db_config["host"]),
        "port": int(resolve_env(db_config.get("port", 5432))),
        "dbname": resolve_env(db_config["dbname"]),
        "user": resolve_env(db_config["user"]),
        "password": resolve_env(db_config["pass"]),
        "sslmode": resolve_env(db_config.get("sslmode", "require")),
        "connect_timeout": 15,
    }

    return psycopg.connect(**connection_config)


# ============================================================
# FETCH POSTS FROM NEON
# ============================================================
def fetch_posts(limit=None):

    query = """
        SELECT
            p.post_id,
            p.post_type,
            p.post_date,
            p.post_url,
            LEFT(
                COALESCE(p.post_content, ''),
                100
            ) AS post_preview

        FROM raw.linkedin_posts AS p

        INNER JOIN raw.linkedin_post_analytics AS a
            ON p.post_id = a.post_id

        WHERE NOT EXISTS (
            SELECT 1
            FROM raw.linkedin_post_media AS m
            WHERE m.post_id = p.post_id
        )

        ORDER BY p.post_date DESC, p.post_id DESC
    """

    if limit is not None:
        query += " LIMIT %s"
        params = (limit,)
    else:
        params = ()

    with get_database_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

    posts = []

    for row in rows:
        posts.append({
            "post_id": row[0],
            "post_type": row[1],
            "post_date": str(row[2]),
            "post_url": row[3],
            "post_preview": row[4],
        })

    return posts


# ============================================================
# FETCH LINKEDIN HTML
# ============================================================

def fetch_html(session, url, timeout=20):

    if not url:
        return None, "missing_url"

    parsed_url = urlparse(url)

    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname not in (
            "www.linkedin.com",
            "linkedin.com"
        )
    ):
        return None, "invalid_linkedin_url"

    try:

        response = session.get(
            url,
            timeout=timeout,
            allow_redirects=True
        )

        status_code = response.status_code

        if status_code != 200:
            return None, f"http_{status_code}"

        final_url = response.url.lower()

        if (
            "/login" in final_url
            or "/checkpoint" in final_url
            or "/authwall" in final_url
        ):
            return None, "authentication_required"

        html = response.text

        if not html.strip():
            return None, "empty_html"

        return html, "ok"

    except requests.exceptions.Timeout:

        return None, "timeout"

    except requests.exceptions.RequestException as error:

        return None, f"request_error:{type(error).__name__}"


# ============================================================
# MEDIA DETECTION
# ============================================================

def classify_html(html, post_id):
    """
    Classify the media format of the original LinkedIn post.

    Uses the public LinkedIn page's main-feed-activity-card
    rather than counting media across the entire webpage.
    """

    soup = BeautifulSoup(html, "html.parser")

    post = soup.select_one("article.main-feed-activity-card")

    if post is None:
        return {
            "content_format": "unknown",
            "confidence": "none",
            "evidence": "post_container_not_found",
            "needs_review": True,
        }

    # --------------------------------------------------
    # VIDEO
    # --------------------------------------------------

    videos = post.select(
        "video, [data-vjs-player='true']"
    )

    if videos:
        return {
            "content_format": "video",
            "confidence": "high",
            "evidence": "video_player_in_original_post",
            "needs_review": False,
        }

    # --------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------

    documents = post.select(
        "button[aria-label='Go to next page of document'], "
        "button[aria-label='Go to previous page of document']"
    )

    if documents:
        return {
            "content_format": "document",
            "confidence": "high",
            "evidence": "document_navigation_in_original_post",
            "needs_review": False,
        }

    # --------------------------------------------------
    # POLL
    # --------------------------------------------------

    polls = post.select(
        "[data-test-id*='poll'], "
        "[class*='poll-option'], "
        "[class*='polls-vote']"
    )

    if polls:
        return {
            "content_format": "poll",
            "confidence": "medium",
            "evidence": "poll_elements_in_original_post",
            "needs_review": True,
        }

    # --------------------------------------------------
    # ORIGINAL POST IMAGES
    # --------------------------------------------------

    image_items = post.select(
        "ul.feed-images-content > li"
    )

    image_count = len(image_items)

    if image_count > 1:
        return {
            "content_format": "multi_image",
            "confidence": "high",
            "evidence": f"{image_count}_original_post_images",
            "needs_review": False,
        }

    if image_count == 1:
        return {
            "content_format": "single_image",
            "confidence": "high",
            "evidence": "1_original_post_image",
            "needs_review": False,
        }

    # --------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------

    return {
        "content_format": "unknown",
        "confidence": "none",
        "evidence": "no_media_attachment_detected",
        "needs_review": True,
    }
def save_results(results):

    fieldnames = [
        "post_id",
        "post_type",
        "post_date",
        "post_url",
        "post_preview",
        "content_format",
        "confidence",
        "evidence",
        "needs_review",
        "fetch_status",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(results)


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
    "--limit",
    type=int,
    default=None,
    help="Maximum posts to classify. Default: all eligible unclassified posts."
)

    parser.add_argument(
        "--timeout",
        type=int,
        default=20
    )

    args = parser.parse_args()

    print("\nLINKEDIN MEDIA CLASSIFIER")
    print("=" * 55)

    print("\nConnecting to Neon using dbt profile...")

    posts = fetch_posts(limit=args.limit)

    print(f"Retrieved {len(posts)} posts from Neon.\n")

    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 "
            "(X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    })

    results = []

    for index, post in enumerate(posts, start=1):

        post_id = post["post_id"]

        post_url = post["post_url"]

        html, fetch_status = fetch_html(
            session,
            post_url,
            timeout=args.timeout
        )

        if html:

            classification = classify_html(
                html,
                post_id
            )

        else:

            classification = {
                "content_format": "unknown",
                "confidence": "none",
                "evidence": "html_unavailable",
                "needs_review": True,
            }

        result = {
            **post,
            **classification,
            "fetch_status": fetch_status,
        }

        results.append(result)

        print(
            f"[{index:02d}/{len(posts):02d}] "
            f"{post_id} | "
            f"{classification['content_format']} | "
            f"{fetch_status} | "
            f"{classification['evidence']}"
        )

        # Small delay between requests.
        if index < len(posts):
            time.sleep(1)

    save_results(results)

    print("\n" + "=" * 55)

    print("CLASSIFICATION SUMMARY")

    summary = {}

    for result in results:

        content_format = result["content_format"]

        summary[content_format] = (
            summary.get(content_format, 0) + 1
        )

    for content_format, count in sorted(summary.items()):

        print(f"{content_format}: {count}")

    print(f"\nResults saved to: {OUTPUT_FILE}")

    print("\nNeon database was not modified.")


if __name__ == "__main__":
    main()