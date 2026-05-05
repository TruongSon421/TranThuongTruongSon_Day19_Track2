"""Feast feature definitions for Lab 19.

Three feature views — one per realistic ML use case from the deck §6:
  - user_profile_features:  stable user attributes (offline-first, daily refresh)
  - item_popularity_features: per-doc/item engagement (mixed batch+stream)
  - query_velocity_features: recent query patterns per user (streaming-friendly)

Run from the repo root after the corpus is seeded:
  cd app/feast_repo
  feast apply
  feast materialize-incremental $(date -u +%Y-%m-%dT%H:%M:%S)

Then in Python:
  from feast import FeatureStore
  fs = FeatureStore(repo_path="app/feast_repo")
  features = fs.get_online_features(
      features=["user_profile_features:reading_speed_wpm",
                "item_popularity_features:click_count_24h",
                "query_velocity_features:queries_last_hour"],
      entity_rows=[{"user_id": "u_001", "doc_id": "cloud_001"}],
  ).to_dict()
"""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from feast import Entity, FeatureView, Field, ValueType
from feast.types import Float32, Int64, String

_REPO_ROOT = Path(__file__).resolve().parent
_DATA_DIR = _REPO_ROOT / "data"
_DATA_DIR.mkdir(exist_ok=True)

# Detect which offline store is configured to pick the right source type.
import yaml as _yaml  # noqa: E402

with open(_REPO_ROOT / "feature_store.yaml") as _f:
    _cfg = _yaml.safe_load(_f)
_offline_type = (_cfg.get("offline_store") or {}).get("type", "file")

if _offline_type == "postgres":
    from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import (
        PostgreSQLSource,
    )

    user_profile_source = PostgreSQLSource(
        name="user_profile_source",
        query="SELECT * FROM feast_user_profile",
        timestamp_field="event_timestamp",
    )
    item_popularity_source = PostgreSQLSource(
        name="item_popularity_source",
        query="SELECT * FROM feast_item_popularity",
        timestamp_field="event_timestamp",
    )
    query_velocity_source = PostgreSQLSource(
        name="query_velocity_source",
        query="SELECT * FROM feast_query_velocity",
        timestamp_field="event_timestamp",
    )
else:
    from feast import FileSource

    user_profile_source = FileSource(
        name="user_profile_source",
        path=str(_DATA_DIR / "user_profile.parquet"),
        timestamp_field="event_timestamp",
    )
    item_popularity_source = FileSource(
        name="item_popularity_source",
        path=str(_DATA_DIR / "item_popularity.parquet"),
        timestamp_field="event_timestamp",
    )
    query_velocity_source = FileSource(
        name="query_velocity_source",
        path=str(_DATA_DIR / "query_velocity.parquet"),
        timestamp_field="event_timestamp",
    )


# ── Entities ────────────────────────────────────────────────────────────
user = Entity(
    name="user",
    join_keys=["user_id"],
    value_type=ValueType.STRING,
    description="A registered user of the AI assistant.",
)

item = Entity(
    name="item",
    join_keys=["doc_id"],
    value_type=ValueType.STRING,
    description="A document in the corpus (matches data/corpus_vn.jsonl doc_id).",
)


# ── Feature views ───────────────────────────────────────────────────────
user_profile_features = FeatureView(
    name="user_profile_features",
    entities=[user],
    ttl=timedelta(days=30),       # stable attrs — daily batch refresh OK
    schema=[
        Field(name="reading_speed_wpm", dtype=Int64),
        Field(name="preferred_language", dtype=String),
        Field(name="topic_affinity", dtype=String),
    ],
    source=user_profile_source,
    online=True,
    description="Stable per-user profile (slow-moving). Refresh: daily.",
)

item_popularity_features = FeatureView(
    name="item_popularity_features",
    entities=[item],
    ttl=timedelta(hours=24),      # popularity decays — keep fresh
    schema=[
        Field(name="click_count_24h", dtype=Int64),
        Field(name="ctr_7d", dtype=Float32),
        Field(name="avg_dwell_seconds", dtype=Float32),
    ],
    source=item_popularity_source,
    online=True,
    description="Per-doc engagement (mixed batch+stream). Refresh: hourly.",
)

query_velocity_features = FeatureView(
    name="query_velocity_features",
    entities=[user],
    ttl=timedelta(hours=1),       # streaming-friendly — sub-second freshness ideal
    schema=[
        Field(name="queries_last_hour", dtype=Int64),
        Field(name="distinct_topics_24h", dtype=Int64),
    ],
    source=query_velocity_source,
    online=True,
    description="Recent query patterns per user (streaming, fraud-style cadence).",
)
