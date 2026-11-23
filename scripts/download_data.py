"""Load Olist CSVs (or a deterministic CI sample) into DuckDB schema 'raw'."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

RAW_DIR = Path("data/raw")
SAMPLE_DIR = Path("data/sample")
WAREHOUSE_PATH = Path("data/warehouse/olist.duckdb")

TABLES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_into_duckdb(source_dir: Path, db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    loaded_at = datetime.now(timezone.utc).isoformat()
    manifest = {"loaded_at": loaded_at, "source_dir": str(source_dir), "tables": {}}

    for table_name, filename in TABLES.items():
        csv_path = source_dir / filename
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Missing {csv_path}. Unzip the 9 Olist CSVs into data/raw/ first."
            )
        con.execute(
            f"""
            CREATE OR REPLACE TABLE raw.{table_name} AS
            SELECT *, TIMESTAMP '{loaded_at}' AS _loaded_at
            FROM read_csv_auto('{csv_path.as_posix()}', header=true, all_varchar=false);
            """
        )
        n_rows = con.execute(f"SELECT COUNT(*) FROM raw.{table_name}").fetchone()[0]
        manifest["tables"][table_name] = {"rows": n_rows, "sha256": sha256_file(csv_path)}

    con.close()
    Path("data/warehouse/ingest_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Loaded {len(TABLES)} tables into {db_path} (schema: raw).")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true")
    args = parser.parse_args()
    load_into_duckdb(SAMPLE_DIR if args.sample else RAW_DIR, WAREHOUSE_PATH)


if __name__ == "__main__":
    main()