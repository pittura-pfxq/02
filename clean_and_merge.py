"""Clean, convert currencies, merge order & customer data, and write to SQLite."""

from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "orders.db"

CONVERSION_RATES = {
    "USD": 6.9,
    "EUR": 7.5,
    "CNY": 1.0,
    "JPY": 0.05,
}


def load_csv_group(pattern: str) -> pd.DataFrame:
    """Load and concatenate all matching .txt files in data/."""
    files = sorted(DATA_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matching '{pattern}' found in {DATA_DIR}")

    frames = []
    for file_path in files:
        df = pd.read_csv(file_path, skipinitialspace=True)
        df.columns = [col.strip() for col in df.columns]
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def clean_and_merge() -> tuple[pd.DataFrame, pd.DataFrame]:
    # 1. Read order and customer data files (supports order.txt, order_new.txt, etc.)
    orders = load_csv_group("order*.txt")
    customers = load_csv_group("customer*.txt")

    # Strip whitespace in string columns
    for df in (orders, customers):
        for col in df.select_dtypes(include=["object", "string"]).columns:
            df[col] = df[col].astype(str).str.strip()

    # 2. Clean duplicates
    orders = orders.drop_duplicates().drop_duplicates(subset=["order_id"], keep="last")
    customers = customers.drop_duplicates().drop_duplicates(subset=["customer_id"], keep="last")

    # 3. Convert amount to CNY using specified conversion rates
    orders["amount"] = pd.to_numeric(orders["amount"], errors="coerce")
    orders["currency"] = orders["currency"].str.upper()

    unknown_currencies = set(orders["currency"].dropna()) - set(CONVERSION_RATES.keys())
    if unknown_currencies:
        raise ValueError(f"Unsupported currencies found: {sorted(unknown_currencies)}")

    orders["amount_cny"] = (
        orders["amount"] * orders["currency"].map(CONVERSION_RATES)
    ).round(2)

    # 4. Merge orders and customers on customer_id
    merged = pd.merge(orders, customers, on="customer_id", how="left")
    merged = merged[
        ["order_id", "customer_id", "customer_name", "region", "amount", "currency", "amount_cny"]
    ].sort_values("order_id").reset_index(drop=True)

    # 5. Create summary table: average amount_cny by region
    summary = (
        merged.groupby("region", as_index=False)
        .agg(
            order_count=("order_id", "count"),
            avg_amount_cny=("amount_cny", "mean"),
        )
        .sort_values("region")
        .reset_index(drop=True)
    )
    summary["avg_amount_cny"] = summary["avg_amount_cny"].round(2)

    # 6. Write merged data and summary table to SQLite database
    with sqlite3.connect(DB_PATH) as conn:
        merged.to_sql("merged_orders", conn, if_exists="replace", index=False)
        summary.to_sql("region_summary", conn, if_exists="replace", index=False)

    print(f"Updated {DB_PATH.name}: {len(merged)} orders, {len(summary)} regions.")
    return merged, summary


if __name__ == "__main__":
    clean_and_merge()
