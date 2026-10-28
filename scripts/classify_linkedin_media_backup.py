#!/usr/bin/env python3
"""Read 20 LinkedIn posts from Neon and attempt evidence-based media classification.

Dependencies: pip install beautifulsoup4 requests psycopg[binary]
Environment: DATABASE_URL or NEON_DATABASE_URL (PostgreSQL connection string).

This script intentionally does not authenticate to LinkedIn, evade access controls,
or write classifications to the database. Unavailable/ambiguous posts remain unknown.
"""
from __future__ import annotations
import yaml
from pathlib import Path
import argparse
import csv
import os
import re
import time
from pathlib import Path

import psycopg
import requests
from bs4 import BeautifulSoup

FORMATS = {"text_only", "single_image", "multi_image", "video", "document", "poll", "link", "unknown"}


def classify_html(html: str, expected_post_id: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
    # A returned LinkedIn page is not necessarily the target post. For public
    # pages, verify that the target post identifier is present in DOM content.
    if not expected_post_id or expected_post_id not in html:
        return dict(content_format="unknown", confidence="none", evidence="target_post_id_not_found_in_html")
    if re.search(r"(?:sign in|join linkedin|log in)\s*[|–-]\s*linkedin", page_title, re.I):
        return dict(content_format="unknown", confidence="none", evidence="login_or_join_page")

    # Strict scoping: LinkedIn HTML is dynamic and the page may include
    # recommendations/comments. We only classify when a unique post container
    # with the requested post ID can be located in the parsed DOM.
    matches = soup.select(f'[data-urn*="{expected_post_id}"], [data-id*="{expected_post_id}"], [id*="{expected_post_id}"]')
    if not matches:
        return dict(content_format="unknown", confidence="none", evidence="target_post_container_not_found")
    # Prefer the deepest match; nested duplicate matches are common.
    root = min(matches, key=lambda e: len(e.select('*')))
    if len(root.select('*')) < 2:
        return dict(content_format="unknown", confidence="none", evidence="post_container_incomplete")

    # Only real DOM nodes count, not serialized localization strings.
    if root.select('[data-vjs-player="true"], video, button[aria-label="Play video"]'):
        return dict(content_format="video", confidence="high", evidence="video_player_dom")
    if root.select('button[aria-label="Go to next page of document"], button[aria-label="Go to previous page of document"]'):
        return dict(content_format="document", confidence="high", evidence="document_viewer_dom")
    if root.select('[role="radiogroup"], [data-test-poll], .polls-vote-results'):
        return dict(content_format="poll", confidence="medium", evidence="poll_dom")

    figures = root.select('figure[role="img"][aria-label="View image"]')
    imgs = root.select('img[alt="View image"]')
    # Count figures first to avoid double-counting img elements inside figures.
    images = len(figures) + sum(not im.find_parent('figure', attrs={'role': 'img'}) for im in imgs)
    if images > 1:
        return dict(content_format="multi_image", confidence="high", evidence=f"{images}_attachment_image_elements")
    if images == 1:
        return dict(content_format="single_image", confidence="high", evidence="1_attachment_image_element")

    # A link in the caption is not necessarily a link-preview attachment.
    # We do not infer link or text-only from absence of detected media.
    return dict(content_format="unknown", confidence="none", evidence="no_conclusive_media_dom;_text_or_link_unverified")


def fetch_html(session: requests.Session, url: str, timeout: int) -> tuple[str | None, str]:
    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        if resp.status_code != 200:
            return None, f"http_{resp.status_code}"
        if "text/html" not in resp.headers.get("Content-Type", "").lower():
            return None, "not_html"
        if "linkedin.com" not in requests.utils.urlparse(resp.url).netloc:
            return None, "redirected_off_linkedin"
        return resp.text, "ok"
    except requests.RequestException as exc:
        return None, f"request_error:{type(exc).__name__}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--output', default='data/processed/linkedin_media_first20.csv')
    parser.add_argument('--delay', type=float, default=2.0, help='Seconds between requests')
    parser.add_argument('--timeout', type=int, default=15)
    args = parser.parse_args()
    if args.limit != 20:
        parser.error('This pilot is intentionally limited to exactly 20 posts; use --limit 20.')
    db_url = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')
    if not db_url:
        raise SystemExit('Missing DATABASE_URL or NEON_DATABASE_URL. Set it in your terminal (do not paste credentials into chat).')
    profile_path = Path.home() / ".dbt" / "profiles.yml"

    if not profile_path.exists():
        raise SystemExit(f"dbt profile not found: {profile_path}")

    with open(profile_path, "r", encoding="utf-8") as f:
        profiles = yaml.safe_load(f)

    profile = profiles["linkedin_intelligence"]
    target_name = profile.get("target", "dev")
    db_config = profile["outputs"][target_name]

    # Resolve environment variables used by dbt
    def resolve(value):
        if isinstance(value, str):
            match = re.fullmatch(
                r"""\{\{\s*env_var\(['"]([^'"]+)['"]\)\s*\}\}""",
                value.strip()
            )

            if match:
                variable = match.group(1)
                value = os.getenv(variable)

                if value is None:
                    raise SystemExit(
                        f"Missing environment variable required by dbt: {variable}"
                    )

        return value

    connection = {
        "host": resolve(db_config["host"]),
        "port": int(resolve(db_config.get("port", 5432))),
        "dbname": resolve(db_config["dbname"]),
        "user": resolve(db_config["user"]),
        "password": resolve(db_config["pass"]),
        "sslmode": "require",
        "connect_timeout": 15,
    }

    with psycopg.connect(**connection) as conn:
      with psycopg.connect(db_url, connect_timeout=15) as conn:
         with conn.cursor() as cur:
            cur.execute('''
                SELECT post_id, post_type, post_date, post_url,
                       LEFT(COALESCE(post_content, ''), 100) AS post_preview
                FROM raw.linkedin_posts
                ORDER BY post_date DESC, post_id DESC
                LIMIT %s
            ''', (args.limit,))
            rows = cur.fetchall()

    if len(rows) != 20:
        print(f'WARNING: retrieved {len(rows)} posts, not 20.')
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (compatible; ResearchMediaFormatPilot/1.0)'})
    results = []
    for index, (post_id, post_type, post_date, post_url, preview) in enumerate(rows, 1):
        outcome = dict(content_format='unknown', confidence='none', evidence='not_fetched')
        fetch_status = 'missing_url'
        if post_url and post_url.startswith('https://www.linkedin.com/'):
            html, fetch_status = fetch_html(session, post_url, args.timeout)
            if html:
                outcome = classify_html(html, post_id)
        elif post_url:
            fetch_status = 'unexpected_url_domain'
        result = {
            'post_id': post_id, 'post_type': post_type,
            'post_date': str(post_date), 'post_url': post_url,
            'post_preview': preview, 'content_format': outcome['content_format'],
            'confidence': outcome['confidence'], 'evidence': outcome['evidence'],
            'fetch_status': fetch_status, 'needs_review': outcome['content_format'] == 'unknown',
        }
        results.append(result)
        print(f"[{index:02d}/{len(rows)}] {post_id}: {result['content_format']} | {fetch_status} | {result['evidence']}")
        if index < len(rows) and args.delay > 0:
            time.sleep(args.delay)

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(results[0]) if results else [
            'post_id', 'post_type', 'post_date', 'post_url', 'post_preview',
            'content_format', 'confidence', 'evidence', 'fetch_status', 'needs_review'])
        writer.writeheader()
        writer.writerows(results)
    print(f'\nSaved {len(results)} rows to {path}')
    print('Classified:', sum(r['content_format'] != 'unknown' for r in results),
          '| Unknown:', sum(r['content_format'] == 'unknown' for r in results))


if __name__ == '__main__':
    main()
