"""Sync NB4 Parquet files → Postgres tables for the docker offline store.

Run this after NB4 cell 2 writes the Parquet files and before `feast apply`:
  python scripts/sync_feast_parquet_to_postgres.py

Tables created (or replaced):
  feast_user_profile, feast_item_popularity, feast_query_velocity
"""
from __future__ import annotations

import sys
from pathlib import Path

import polars as pl
import psycopg

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "app" / "feast_repo" / "data"

DSN = "postgresql://feast:feast@localhost:5432/feast_offline"

TABLES = [
    ("user_profile.parquet", "feast_user_profile"),
    ("item_popularity.parquet", "feast_item_popularity"),
    ("query_velocity.parquet", "feast_query_velocity"),
]


def _polars_to_pg_type(dtype: pl.DataType) -> str:
    if dtype == pl.Int64:
        return "BIGINT"
    if dtype in (pl.Float32, pl.Float64):
        return "DOUBLE PRECISION"
    if dtype == pl.Boolean:
        return "BOOLEAN"
    if isinstance(dtype, pl.Datetime):
        return "TIMESTAMPTZ"
    return "TEXT"


def sync_table(conn: psycopg.Connection, parquet_path: Path, table: str) -> None:
    df = pl.read_parquet(parquet_path)

    col_defs = ", ".join(
        f'"{col}" {_polars_to_pg_type(dtype)}'
        for col, dtype in zip(df.columns, df.dtypes)
    )
    with conn.cursor() as cur:
        cur.execute(f'DROP TABLE IF EXISTS "{table}"')
        cur.execute(f'CREATE TABLE "{table}" ({col_defs})')

        rows = df.to_pandas().itertuples(index=False, name=None)
        placeholders = ", ".join(["%s"] * len(df.columns))
        cur.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', rows)

    conn.commit()
    print(f"  {table}: {len(df)} rows from {parquet_path.name}")


def main() -> int:
    missing = [p for name, _ in TABLES if not (p := DATA_DIR / name).exists()]
    if missing:
        print("ERROR: Parquet files not found. Run NB4 cell 2 first:")
        for p in missing:
            print(f"  {p}")
        return 1

    print(f"Connecting to {DSN} ...")
    with psycopg.connect(DSN) as conn:
        for parquet_name, table in TABLES:
            sync_table(conn, DATA_DIR / parquet_name, table)

    print("Done — 3 tables synced to Postgres offline store.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
