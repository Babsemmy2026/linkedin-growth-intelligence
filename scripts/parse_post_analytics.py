from pathlib import Path
import pandas as pd
import re

# Existing project folders
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "raw" / "post_analytics"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

METRICS = {
    "Impressions": "impressions",
    "Members reached": "reach",
    "Reactions": "reactions",
    "Comments": "comments",
    "Reposts": "reposts",
    "Saves": "saves",
    "Sends on LinkedIn": "sends",
    "Followers gained from this post": "followers_gained",
    "Profile viewers from this post": "profile_viewers",
}


def parse_analytics(file_path):
    df = pd.read_excel(
        file_path,
        sheet_name="Post analytics",
        header=None,
        dtype=str
    )

    # Convert the first two columns into key-value pairs
    values = {}

    for _, row in df.iterrows():
        key = row.iloc[0]
        value = row.iloc[1]

        if pd.notna(key):
            values[str(key).strip()] = value

    post_url = values.get("Post URL")

    if not post_url or pd.isna(post_url):
        raise ValueError("Post URL missing")

    match = re.search(r"(?:ugcPost|activity|share)-(\d+)", post_url)

    result = {
        "post_id": match.group(1) if match else None,
        "post_url": post_url,
        "post_date": values.get("Post Date"),
        "source_file": file_path.name,
    }

    for excel_name, column_name in METRICS.items():
        value = values.get(excel_name)

        if value is None or pd.isna(value):
            result[column_name] = None
        else:
            result[column_name] = int(
                str(value).replace(",", "").strip()
            )

    return result


def main():
    files = sorted(INPUT_DIR.glob("*.xlsx"))

    if not files:
        print("No Excel analytics files found.")
        return

    records = []

    for file_path in files:
        try:
            record = parse_analytics(file_path)
            records.append(record)
            print(f"Processed: {file_path.name}")
        except Exception as error:
            print(f"Failed: {file_path.name}: {error}")

    if not records:
        print("No files processed successfully.")
        return

    result = pd.DataFrame(records)

    output_file = OUTPUT_DIR / "post_analytics_parsed.csv"
    result.to_csv(output_file, index=False)

    print("\nProcessing complete!")
    print(f"Posts processed: {len(result)}")
    print(f"Output: {output_file}")

    print("\nExtracted metrics:")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()