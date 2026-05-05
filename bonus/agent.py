"""HybridMemoryAgent — combines Qdrant episodic memory + Feast user profile.

Reuses patterns from NB2 (hybrid RRF search) and NB4 (Feast online lookup).
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastembed import TextEmbedding
from rank_bm25 import BM25Okapi
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

COLLECTION = "lab19_episodic"
VECTOR_SIZE = 384
RRF_K = 60
TOP_K = 3


def _chunks(text: str, max_chars: int = 200) -> list[str]:
    parts = [s.strip() for s in text.split(". ") if s.strip()]
    result: list[str] = []
    buf = ""
    for part in parts:
        candidate = (buf + ". " + part).strip() if buf else part
        if len(candidate) <= max_chars:
            buf = candidate
        else:
            if buf:
                result.append(buf)
            buf = part
    if buf:
        result.append(buf)
    return result or [text[:max_chars]]


class HybridMemoryAgent:
    def __init__(
        self,
        feast_repo_path: str,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
    ) -> None:
        self._feast_repo_path = feast_repo_path
        self._embedder = TextEmbedding("BAAI/bge-small-en-v1.5")

        try:
            self._qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
            self._qdrant.get_collections()  # probe
        except Exception:
            # Fallback: in-memory Qdrant when Docker stack is not running
            self._qdrant = QdrantClient(":memory:")

        if COLLECTION not in {c.name for c in self._qdrant.get_collections().collections}:
            self._qdrant.create_collection(
                COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

        # In-memory BM25 corpus per user: {user_id: [(doc_id, text), ...]}
        self._corpus: dict[str, list[tuple[str, str]]] = defaultdict(list)

        self._fs: Any = None  # lazy-init Feast

    def _get_feast(self) -> Any:
        if self._fs is None:
            try:
                from feast import FeatureStore
                self._fs = FeatureStore(repo_path=self._feast_repo_path)
            except Exception:
                self._fs = None
        return self._fs

    def _get_profile(self, user_id: str) -> dict[str, Any]:
        fs = self._get_feast()
        if fs is None:
            return {"topic_affinity": "ai_ml", "reading_speed_wpm": 200,
                    "queries_last_hour": 5, "distinct_topics_24h": 3}
        try:
            result = fs.get_online_features(
                features=[
                    "user_profile_features:topic_affinity",
                    "user_profile_features:reading_speed_wpm",
                    "query_velocity_features:queries_last_hour",
                    "query_velocity_features:distinct_topics_24h",
                ],
                entity_rows=[{"user_id": user_id}],
            ).to_dict()
            return {k: v[0] for k, v in result.items() if k != "user_id"}
        except Exception:
            return {"topic_affinity": "ai_ml", "reading_speed_wpm": 200,
                    "queries_last_hour": 5, "distinct_topics_24h": 3}

    def remember(self, text: str, user_id: str = "u_001") -> None:
        chunks = _chunks(text)
        vectors = list(self._embedder.embed(chunks))
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec.tolist(),
                payload={
                    "user_id": user_id,
                    "text": chunk,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            for chunk, vec in zip(chunks, vectors)
        ]
        self._qdrant.upsert(COLLECTION, points=points)
        for chunk in chunks:
            self._corpus[user_id].append((str(uuid.uuid4()), chunk))

    def recall(self, query: str, user_id: str = "u_001") -> str:
        profile = self._get_profile(user_id)

        # 1. Semantic search in Qdrant filtered by user_id
        query_vec = next(self._embedder.embed([query])).tolist()
        sem_hits = self._qdrant.search(
            COLLECTION,
            query_vector=query_vec,
            query_filter=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]),
            limit=TOP_K * 3,
            with_payload=True,
        )
        sem_ids = [h.payload["text"] for h in sem_hits]  # text as ID proxy for RRF

        # 2. BM25 search on in-memory corpus for this user
        corpus_items = self._corpus.get(user_id, [])
        bm25_ids: list[str] = []
        if corpus_items:
            tokenized = [text.lower().split() for _, text in corpus_items]
            bm25 = BM25Okapi(tokenized)
            scores = bm25.get_scores(query.lower().split())
            ranked = sorted(range(len(corpus_items)), key=lambda i: scores[i], reverse=True)
            bm25_ids = [corpus_items[i][1] for i in ranked[: TOP_K * 3]]

        # 3. RRF merge
        rrf_scores: dict[str, float] = defaultdict(float)
        for rank, text in enumerate(sem_ids, 1):
            rrf_scores[text] += 1.0 / (RRF_K + rank)
        for rank, text in enumerate(bm25_ids, 1):
            rrf_scores[text] += 1.0 / (RRF_K + rank)

        top_memories = sorted(rrf_scores, key=rrf_scores.__getitem__, reverse=True)[:TOP_K]

        # 4. Assemble context
        mem_block = "\n".join(f"  - {m}" for m in top_memories) if top_memories else "  (no memories yet)"
        context = (
            f"User profile [{user_id}]:\n"
            f"  topic_affinity={profile.get('topic_affinity')} | "
            f"reading_speed={profile.get('reading_speed_wpm')}wpm | "
            f"queries_last_hour={profile.get('queries_last_hour')} | "
            f"distinct_topics_24h={profile.get('distinct_topics_24h')}\n"
            f"Top memories (hybrid RRF):\n{mem_block}"
        )
        return context


def _default_feast_path() -> str:
    return str(Path(__file__).resolve().parent.parent / "app" / "feast_repo")
