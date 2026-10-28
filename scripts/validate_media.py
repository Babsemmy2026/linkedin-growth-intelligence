#!/usr/bin/env python3

"""
LinkedIn Media Validation

Validates media types detected from public LinkedIn post HTML
against the user's LinkedIn Rich_Media.csv export.

Primary dataset:
    data/raw/Shares_970632177.csv

Validation dataset:
    Rich_Media.csv

Output:
    data/processed/rich_media_validation.csv

Uses Python standard library only.
No LinkedIn authentication or API credentials required.
"""

import argparse
import csv
import html
import json
import re
import time
import urllib.error
import urllib.request

from collections import Counter
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SHARES_PATH = PROJECT_ROOT / "data/raw/Shares_970632177.csv"

OUTPUT_DIR = PROJECT_ROOT / "data/processed"

VALIDATION_OUTPUT = OUTPUT_DIR / "rich_media_validation.csv"

CACHE_PATH = OUTPUT_DIR / "linkedin_media_cache.json"

USER_AGENT = "Mozilla/5.0"


# --------------------------------------------------
# 1. READ CSV FILES
# --------------------------------------------------

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


# --------------------------------------------------
# 2. PARSE LINKEDIN DATES
# --------------------------------------------------

def parse_share_date(value):
    return datetime.strptime(
        value.strip(),
        "%Y-%m-%d %H:%M:%S"
    )


def parse_rich_media_date(value):
    """
    Example:
    You uploaded a feed photo on October 20, 2026
    at 7:36 AM (GMT)
    """

    pattern = (
        r"You uploaded (?:an? )?(.+?) on "
        r"([A-Za-z]+ \d{1,2}, \d{4}) "
        r"at (\d{1,2}:\d{2} [AP]M)"
    )

    match = re.search(pattern, value, re.IGNORECASE)

    if not match:
        return None, None

    media_type = match.group(1).strip().lower()

    date_text = match.group(2) + " " + match.group(3)

    date_value = datetime.strptime(
        date_text,
        "%B %d, %Y %I:%M %p"
    )

    return date_value, media_type


# --------------------------------------------------
# 3. NORMALIZE MEDIA TYPES FOR COMPARISON
# --------------------------------------------------

def normalize_linkedin_type(value):
    """
    Preserve the original LinkedIn label separately.

    These mappings are used only for comparison.
    """

    mapping = {
        "feed photo": "image",
        "photo": "image",
        "video": "video",
        "feed video": "video",
        "document": "document",
        "feed document": "document",
    }

    return mapping.get(value.lower().strip(), "unknown")


# --------------------------------------------------
# 4. EXTRACT MEDIA FROM ORIGINAL POST HTML
# --------------------------------------------------

class LinkedInMediaParser(HTMLParser):

    VOID_TAGS = {
        "area", "base", "br", "col", "embed",
        "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"
    }

    def __init__(self):
        super().__init__()

        self.stack = []

        self.in_original = False

        self.original_depth = None

        self.gallery_depth = None

        self.images = set()
        self.videos = set()
        self.documents = set()

        self.original_found = False

    def handle_starttag(self, tag, attrs):

        attributes = dict(attrs)

        classes = attributes.get("class") or ""

        class_tokens = set(classes.split())

        is_original = (
            tag == "article"
            and "main-feed-activity-card" in class_tokens
            and "related-posts__crosslink" not in class_tokens
            and not self.original_found
        )

        if is_original:
            self.in_original = True
            self.original_found = True
            self.original_depth = len(self.stack)

        if self.in_original:

            if "feed-images-content" in class_tokens:
                self.gallery_depth = len(self.stack)

            if tag == "img" and self.gallery_depth is not None:

                image_url = (
                    attributes.get("data-delayed-url")
                    or attributes.get("src")
                    or ""
                )

                if "media.licdn.com/dms/image/" in image_url:

                    clean_url = image_url.split("?")[0]

                    self.images.add(clean_url)

            elif tag == "video":

                video_id = (
                    attributes.get("data-digitalmedia-asset-urn")
                    or "native_video"
                )

                self.videos.add(video_id)

            elif tag == "iframe":

                if (
                    attributes.get("data-id")
                    == "feed-paginated-document-content"
                ):

                    document_url = (
                        attributes.get("data-delayed-url")
                        or "native_document"
                    )

                    self.documents.add(document_url)

        if tag not in self.VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):

        if tag in self.VOID_TAGS:
            return

        # Recover from occasional mismatched HTML tags.
        if tag in self.stack:
            while self.stack:
                popped = self.stack.pop()
                if popped == tag:
                    break

        if (
            self.gallery_depth is not None
            and len(self.stack) <= self.gallery_depth
        ):
            self.gallery_depth = None

        if (
            self.in_original
            and self.original_depth is not None
            and len(self.stack) <= self.original_depth
        ):
            self.in_original = False

    def result(self):

        if not self.original_found:
            return {
                "detected_media_type": "unknown",
                "image_count": 0,
                "video_count": 0,
                "document_count": 0,
                "original_post_found": False,
            }

        if self.documents:
            media_type = "document"

        elif self.videos:
            media_type = "video"

        elif len(self.images) > 1:
            media_type = "multi_image"

        elif len(self.images) == 1:
            media_type = "image"

        else:
            media_type = "unknown"

        return {
            "detected_media_type": media_type,
            "image_count": len(self.images),
            "video_count": len(self.videos),
            "document_count": len(self.documents),
            "original_post_found": True,
        }


# --------------------------------------------------
# 5. FETCH PUBLIC POST
# --------------------------------------------------

def inspect_post(url):

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            page_html = response.read().decode(
                "utf-8",
                errors="replace"
            )

        parser = LinkedInMediaParser()

        parser.feed(page_html)

        result = parser.result()

        result["fetch_status"] = "success"

        return result

    except urllib.error.HTTPError as error:

        return {
            "detected_media_type": "unknown",
            "image_count": 0,
            "video_count": 0,
            "document_count": 0,
            "original_post_found": False,
            "fetch_status": f"http_{error.code}",
        }

    except Exception as error:

        return {
            "detected_media_type": "unknown",
            "image_count": 0,
            "video_count": 0,
            "document_count": 0,
            "original_post_found": False,
            "fetch_status": type(error).__name__,
        }


# --------------------------------------------------
# 6. MATCH RICH MEDIA TO POSTS
# --------------------------------------------------

def match_rich_media(shares, rich_media, tolerance_minutes=5):

    matched_records = []

    for record in rich_media:

        raw_description = record.get("Date/Time", "")

        media_date, media_type = parse_rich_media_date(
            raw_description
        )

        if media_date is None:

            matched_records.append({
                "rich_media_date": raw_description,
                "linkedin_original_media_type": "unknown",
                "matched_post_url": "",
                "match_status": "unparsed_date",
                "time_difference_seconds": "",
            })

            continue

        candidates = []

        for post in shares:

            try:
                post_date = parse_share_date(
                    post["Date"]
                )
            except (ValueError, KeyError):
                continue

            difference = abs(
                (post_date - media_date).total_seconds()
            )

            if difference <= tolerance_minutes * 60:

                candidates.append(
                    (difference, post)
                )

        candidates.sort(key=lambda x: x[0])

        if len(candidates) == 1:

            difference, post = candidates[0]

            matched_records.append({
                "rich_media_date": raw_description,
                "linkedin_original_media_type": media_type,
                "matched_post_url": post["ShareLink"],
                "match_status": "matched",
                "time_difference_seconds": difference,
            })

        elif len(candidates) > 1:

            matched_records.append({
                "rich_media_date": raw_description,
                "linkedin_original_media_type": media_type,
                "matched_post_url": "",
                "match_status": "ambiguous",
                "time_difference_seconds": "",
            })

        else:

            matched_records.append({
                "rich_media_date": raw_description,
                "linkedin_original_media_type": media_type,
                "matched_post_url": "",
                "match_status": "no_match",
                "time_difference_seconds": "",
            })

    return matched_records


# --------------------------------------------------
# 7. LOAD AND SAVE CACHE
# --------------------------------------------------

def load_cache():

    if CACHE_PATH.exists():

        with open(CACHE_PATH, encoding="utf-8") as file:
            return json.load(file)

    return {}


def save_cache(cache):

    with open(CACHE_PATH, "w", encoding="utf-8") as file:

        json.dump(
            cache,
            file,
            indent=2
        )


# --------------------------------------------------
# 8. VALIDATE MEDIA TYPES
# --------------------------------------------------

def validate_records(records, cache, delay=2):

    results = []

    for index, record in enumerate(records, 1):

        url = record["matched_post_url"]

        result = dict(record)

        if record["match_status"] != "matched":

            result.update({
                "detected_media_type": "unknown",
                "validation_status": "not_comparable",
                "image_count": 0,
                "video_count": 0,
                "document_count": 0,
                "fetch_status": "not_fetched",
            })

            results.append(result)

            continue

        print(
            f"[{index}/{len(records)}] Inspecting {url}"
        )

        if url in cache:

            detected = cache[url]

        else:

            detected = inspect_post(url)

            cache[url] = detected

            save_cache(cache)

            time.sleep(delay)

        result.update(detected)

        original_type = normalize_linkedin_type(
            record["linkedin_original_media_type"]
        )

        detected_type = detected["detected_media_type"]

        if (
            original_type == "unknown"
            or detected_type == "unknown"
        ):

            validation_status = "not_comparable"

        elif original_type == detected_type:

            validation_status = "match"

        elif (
            original_type == "image"
            and detected_type == "multi_image"
        ):

            validation_status = "needs_review"

        else:

            validation_status = "mismatch"

        result["validation_status"] = validation_status

        results.append(result)

    return results


# --------------------------------------------------
# 9. SAVE VALIDATION REPORT
# --------------------------------------------------

def save_validation_report(records):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    columns = [
        "rich_media_date",
        "linkedin_original_media_type",
        "matched_post_url",
        "match_status",
        "time_difference_seconds",
        "detected_media_type",
        "validation_status",
        "image_count",
        "video_count",
        "document_count",
        "original_post_found",
        "fetch_status",
    ]

    with open(
        VALIDATION_OUTPUT,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore"
        )

        writer.writeheader()

        writer.writerows(records)


# --------------------------------------------------
# 10. MAIN
# --------------------------------------------------

def main():

    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument(
        "--rich",
        required=True,
        help="Path to Rich_Media.csv"
    )

    argument_parser.add_argument(
        "--delay",
        type=float,
        default=2.0
    )

    args = argument_parser.parse_args()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\nLINKEDIN MEDIA VALIDATION")
    print("=" * 50)

    shares = read_csv(SHARES_PATH)

    rich_media = read_csv(
        Path(args.rich).expanduser()
    )

    print(f"Posts loaded: {len(shares)}")
    print(f"Rich Media records loaded: {len(rich_media)}")

    matched = match_rich_media(
        shares,
        rich_media
    )

    match_summary = Counter(
        record["match_status"]
        for record in matched
    )

    print("\nMATCHING SUMMARY")

    for status, count in match_summary.items():
        print(f"{status}: {count}")

    cache = load_cache()

    validated = validate_records(
        matched,
        cache,
        delay=args.delay
    )

    save_validation_report(validated)

    validation_summary = Counter(
        record["validation_status"]
        for record in validated
    )

    print("\nVALIDATION STATUS")
    print("-" * 50)

    for status, count in validation_summary.items():
        print(f"{status}: {count}")

    print("\nReport saved to:")
    print(VALIDATION_OUTPUT)

    print("\nValidation completed.")


if __name__ == "__main__":
    main()
