from pathlib import Path
from datetime import datetime, timezone
import subprocess
import sys
import time
import shutil
import tempfile

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
QUEUE = BASE / "data/processed/analytics_collection_queue.csv"
PARSED = BASE / "data/processed/post_analytics_parsed.csv"
DOWNLOADS = Path.home() / "Downloads"
DESTINATION = BASE / "data/raw/post_analytics"

DESTINATION.mkdir(parents=True, exist_ok=True)


def get_pending_posts():
    queue = pd.read_csv(QUEUE, dtype=str)
    return queue.loc[queue["status"] == "pending"].copy()


def downloaded_files():
    return {
        p.resolve()
        for p in DOWNLOADS.glob("*.xlsx")
        if p.is_file()
    }


def process_single_report(report_path, expected_post_id):
    """
    Validate one Excel analytics report using the existing parser.
    Record the collection timestamp only after successful parsing
    and post-ID verification.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_base = Path(temp_dir)

        temp_raw = temp_base / "data/raw/post_analytics"
        temp_processed = temp_base / "data/processed"

        temp_raw.mkdir(parents=True)
        temp_processed.mkdir(parents=True)

        temp_report = temp_raw / report_path.name
        shutil.copy2(report_path, temp_report)

        parser_path = BASE / "scripts/parse_post_analytics.py"
        parser_code = parser_path.read_text()

        original = "Path(__file__).resolve().parent.parent"

        if original not in parser_code:
            raise RuntimeError(
                "Parser structure differs from the expected version. "
                "No data has been modified."
            )

        isolated_code = parser_code.replace(
            original,
            f"Path({str(temp_base)!r})"
        )

        isolated_parser = temp_base / "parse_post_analytics.py"
        isolated_parser.write_text(isolated_code)

        subprocess.run(
            [sys.executable, str(isolated_parser)],
            check=True
        )

        isolated_output = (
            temp_processed / "post_analytics_parsed.csv"
        )

        if not isolated_output.exists():
            raise RuntimeError(
                "Parser did not produce an output file."
            )

        new_data = pd.read_csv(
            isolated_output,
            dtype=str
        )

        if len(new_data) != 1:
            raise RuntimeError(
                f"Expected 1 analytics record, got {len(new_data)}."
            )

        actual_post_id = str(new_data.iloc[0]["post_id"])

        if actual_post_id != expected_post_id:
            raise RuntimeError(
                f"Post mismatch! Expected {expected_post_id}, "
                f"but report belongs to {actual_post_id}."
            )

        # Record when this report was successfully collected
        # and validated. Store the timestamp in UTC.
        collected_at = datetime.now(timezone.utc).isoformat()

        new_data["collected_at"] = collected_at
        new_data["timestamp_source"] = "collector_clock"

        if PARSED.exists():
            existing = pd.read_csv(PARSED, dtype=str)

            combined = pd.concat(
                [existing, new_data],
                ignore_index=True
            )
        else:
            combined = new_data

        # Keep the latest processed record for each post.
        combined = combined.drop_duplicates(
            subset=["post_id"],
            keep="last"
        )

        combined.to_csv(PARSED, index=False)

        print(f"Verified post ID: {actual_post_id}")
        print(f"Collected at (UTC): {collected_at}")
        print("Timestamp source: collector_clock")
        print("Metrics and timestamp saved successfully.")


def refresh_queue():
    subprocess.run(
        [
            sys.executable,
            str(BASE / "scripts/prepare_analytics_collection.py")
        ],
        check=True
    )

    queue = pd.read_csv(QUEUE, dtype=str)

    collected = (queue["status"] == "collected").sum()
    remaining = (queue["status"] == "pending").sum()

    print("\nCOLLECTION PROGRESS")
    print(f"Collected: {collected}")
    print(f"Remaining: {remaining}")


def collect():
    print("\nLINKEDIN ANALYTICS COLLECTION ASSISTANT")
    print("=" * 50)

    while True:
        pending = get_pending_posts()

        if pending.empty:
            print("\nAll posts have analytics!")
            break

        post = pending.iloc[0]

        post_id = str(post["post_id"])
        post_url = str(post["post_url"])

        print(f"\nPosts remaining: {len(pending)}")
        print(f"POST ID: {post_id}")
        print(f"POST URL: {post_url}")

        before = downloaded_files()

        subprocess.Popen(
            ["firefox", post_url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        print("\nIn Firefox:")
        print("1. Click View analytics.")
        print("2. Download the Excel analytics report.")
        print("3. Return here and press ENTER.")
        print("   Type 'unavailable' if View analytics is missing.")
        print("   Type 'skip' or 'quit' if needed.")

        response = input("\nYour choice: ").strip().lower()

        if response == "quit":
            print("Collection stopped.")
            break

        if response == "unavailable":
            unavailable_file = (
                BASE / "data/processed/unavailable_analytics.csv"
            )

            record = pd.DataFrame([{
                "post_id": post_id,
                "checked_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }])

            if unavailable_file.exists():
                existing = pd.read_csv(
                    unavailable_file,
                    dtype=str
                )

                record = pd.concat(
                    [existing, record],
                    ignore_index=True
                )

            record = record.drop_duplicates(
                subset=["post_id"],
                keep="last"
            )

            record.to_csv(
                unavailable_file,
                index=False
            )

            print(f"Marked unavailable: {post_id}")

            refresh_queue()
            continue

        if response == "skip":
            print("Post skipped for now.")
            print("Restart later to retry this post.")
            break

        time.sleep(1)

        after = downloaded_files()
        new_files = sorted(after - before)

        if len(new_files) != 1:
            print(
                f"Expected 1 new Excel report, found {len(new_files)}."
            )
            print("Post remains pending.")
            print("Stopping safely. Restart when ready.")
            break

        file = new_files[0]

        target = DESTINATION / file.name

        if target.exists():
            target = DESTINATION / f"{post_id}_{file.name}"

        try:
            # Validate and parse before moving the report.
            process_single_report(file, post_id)

            shutil.move(str(file), str(target))

            print(f"Saved report: {target}")

            refresh_queue()

        except Exception as exc:
            print(f"\nERROR: {exc}")
            print("Report was not moved.")
            print("Please inspect the error before continuing.")
            break

    print("\nCollection session finished.")


if __name__ == "__main__":
    collect()