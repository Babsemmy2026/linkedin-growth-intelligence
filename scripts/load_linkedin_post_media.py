import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from classify_linkedin_media import get_database_connection


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CSV_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "linkedin_media_first20.csv"
)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw.linkedin_post_media (
    post_id TEXT PRIMARY KEY,
    content_format TEXT NOT NULL,
    media_count INTEGER,
    confidence TEXT,
    evidence TEXT,
    needs_review BOOLEAN DEFAULT TRUE,
    classified_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

INSERT_SQL = """
INSERT INTO raw.linkedin_post_media (
    post_id,
    content_format,
    media_count,
    confidence,
    evidence,
    needs_review
)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (post_id)
DO UPDATE SET
    content_format = EXCLUDED.content_format,
    media_count = EXCLUDED.media_count,
    confidence = EXCLUDED.confidence,
    evidence = EXCLUDED.evidence,
    needs_review = EXCLUDED.needs_review,
    classified_at = CURRENT_TIMESTAMP;
"""


def get_media_count(content_format, evidence):

    if content_format == "single_image":
        return 1

    if content_format == "multi_image":
        return int(evidence.split("_")[0])

    if content_format in ("video", "document"):
        return 1

    if content_format == "text_only":
        return 0

    return None


def main():

    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"Classification file not found: {CSV_FILE}"
        )

    with open(CSV_FILE, newline="", encoding="utf-8") as file:
        records = list(csv.DictReader(file))

    if not records:
        raise ValueError("Classification CSV is empty.")

    with get_database_connection() as conn:

        with conn.cursor() as cursor:

            cursor.execute(CREATE_TABLE_SQL)

            for row in records:

                content_format = row["content_format"]
                evidence = row["evidence"]

                media_count = get_media_count(
                    content_format,
                    evidence
                )

                needs_review = (
                    row["needs_review"].strip().lower()
                    == "true"
                )

                cursor.execute(
                    INSERT_SQL,
                    (
                        row["post_id"],
                        content_format,
                        media_count,
                        row["confidence"],
                        evidence,
                        needs_review,
                    )
                )

        conn.commit()

    print(
        f"Successfully loaded {len(records)} "
        "media classifications into Neon."
    )


if __name__ == "__main__":
    main()