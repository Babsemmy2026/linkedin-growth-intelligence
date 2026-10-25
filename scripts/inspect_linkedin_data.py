from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
FILE_PATH = BASE_DIR / "data/raw/Shares_970632177.csv"

df = pd.read_csv(FILE_PATH)

print("\nTotal posts:", len(df))
print("\nColumns:", df.columns.tolist())

print("\nFirst five posts:")
print(df[["Date", "ShareLink"]].head().to_string(index=False))

print("\nMissing post links:", df["ShareLink"].isna().sum())
print("Unique post links:", df["ShareLink"].nunique())