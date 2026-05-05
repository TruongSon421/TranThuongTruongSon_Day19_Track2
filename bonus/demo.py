"""5-query demo for HybridMemoryAgent.

Run: python bonus/demo.py
Expected: exits 0, prints assembled context for each query.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bonus.agent import HybridMemoryAgent, _default_feast_path

MEMORIES = [
    "Kubernetes là hệ thống orchestration container mã nguồn mở. "
    "Nó tự động scale pod khi CPU vượt threshold. "
    "Horizontal Pod Autoscaler dựa trên metrics server.",
    "Cloud security bao gồm IAM policies, network segmentation và encryption at rest. "
    "Zero-trust model yêu cầu verify mọi request kể cả internal traffic.",
    "Infrastructure as Code với Terraform cho phép tự động mở rộng hạ tầng. "
    "Auto-scaling group trên AWS dựa trên CloudWatch alarm.",
    "Vector database như Qdrant lưu embedding để tìm kiếm ngữ nghĩa. "
    "Hybrid search kết hợp BM25 và dense retrieval qua RRF.",
    "Feature store như Feast tách biệt offline training data và online serving. "
    "TTL của feature view quyết định freshness — query_velocity dùng TTL=1h.",
]

QUERIES = [
    ("Tôi đã đọc gì về Kubernetes?",
     "vector hit — keyword 'Kubernetes' in memory"),
    ("Recommend đọc gì tiếp",
     "uses topic_affinity from Feast profile"),
    ("Tôi đang quan tâm gì gần đây?",
     "uses queries_last_hour from query_velocity_features"),
    ("Tài liệu về tự động mở rộng hạ tầng?",
     "paraphrase — no literal 'Kubernetes', vector wins"),
    ("Cho tôi summary cloud security",
     "hybrid + profile: episodic memory + topic_affinity context"),
]


def main() -> int:
    agent = HybridMemoryAgent(feast_repo_path=_default_feast_path())

    print("=== Seeding 5 memories for u_001 ===")
    for mem in MEMORIES:
        agent.remember(mem, user_id="u_001")
    print(f"Seeded {len(MEMORIES)} memories.\n")

    for i, (query, note) in enumerate(QUERIES, 1):
        print(f"--- Query {i}: {query}")
        print(f"    [{note}]")
        context = agent.recall(query, user_id="u_001")
        print(context)
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
