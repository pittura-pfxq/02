"""Flask frontend connected to the SQLite database produced by clean_and_merge.py."""

from datetime import datetime
from pathlib import Path
import sqlite3
from flask import Flask, jsonify, render_template

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "orders.db"

app = Flask(__name__)


def fetch_tables() -> tuple[list[dict], list[dict], str]:
    """Read fresh data from SQLite on every request so updates appear automatically."""
    if not DB_PATH.exists():
        return [], [], "Database not found"

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        orders = [
            dict(row)
            for row in conn.execute(
                "SELECT order_id, customer_id, customer_name, region, amount, currency, amount_cny "
                "FROM merged_orders ORDER BY order_id"
            ).fetchall()
        ]
        summary = [
            dict(row)
            for row in conn.execute(
                "SELECT region, order_count, avg_amount_cny "
                "FROM region_summary ORDER BY region"
            ).fetchall()
        ]

    updated_at = datetime.fromtimestamp(DB_PATH.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    return orders, summary, updated_at


@app.route("/")
def index():
    orders, summary, updated_at = fetch_tables()
    return render_template(
        "index.html",
        orders=orders,
        summary=summary,
        updated_at=updated_at,
    )


@app.route("/api/data")
def api_data():
    orders, summary, updated_at = fetch_tables()
    return jsonify(
        {
            "orders": orders,
            "summary": summary,
            "updated_at": updated_at,
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
