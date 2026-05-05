# Day 19 — Vector Store + Feature Store Lab (Track 2)

Lab cho **AICB-P2T2 · Ngày 19 · Vector Store + Feature Store**.
Build hybrid search API + Feast feature store hoàn chỉnh, đo Precision@10 và P99 latency.

**Hai paths để chọn:**

| Path | Stack | Setup | RAM | Khi nào dùng |
|---|---|---|---|---|
| **Lite (default)** | `fastembed` + Qdrant in-memory + SQLite Feast + FastAPI | `bash setup-lite.sh` (~60 s) | ~700 MB | Hầu hết học viên — laptop yếu, không Docker, focus vào concept |
| **Docker (full)** | Qdrant server + Redis + Postgres + bge-m3 | `bash setup-docker.sh` (~3 min) | ~3 GB | Học viên muốn trải nghiệm production stack thật, có Docker Desktop |

> Cả hai paths dùng **cùng `qdrant-client` API và Feast definitions** — bạn có
> thể đổi giữa hai paths bất cứ lúc nào bằng cách đổi `QDRANT_MODE` trong `.env`.

---

## Quick Start — Lite (recommended)

```bash
git clone https://github.com/<your-username>/Day19-Track2-VectorFeatureStore-Lab.git
cd Day19-Track2-VectorFeatureStore-Lab
bash setup-lite.sh    # ~60 s — venv + deps + seed corpus + smoke test
make api &            # FastAPI on :8000
make benchmark        # Precision@10 + latency table
make lab              # Jupyter Lab on :8888
```

Yêu cầu: **Python ≥ 3.10**. Không cần Docker, không cần GPU, không cần OpenAI key.

Khi `setup-lite.sh` báo `All checks passed`, mở
**http://localhost:8888/lab/tree/01_embeddings_index.ipynb** và bắt đầu.

### Tất cả lệnh `make`

```
make setup-lite      Lite: venv + deps + seed + smoke
make verify-lite     Lite: 5-second smoke test
make seed            Both: regenerate data/ files
make api             Lite: FastAPI on :8000
make lab             Lite: Jupyter Lab on :8888
make benchmark       Both: Precision@10 + P99 latency table
make test            Both: pytest
make clean-lite      Lite: wipe venv + data + Feast registry

make setup-docker    Docker: full stack + venv + seed
make verify-docker   Docker: verify Qdrant/Redis/Postgres reachable
make docker-up       Docker: just bring services up
make docker-down     Docker: stop services (data persists)
make docker-clean    Docker: stop + wipe volumes
```

---

## Quick Start — Docker (full stack)

```bash
bash setup-docker.sh    # ~3 min on first run (image pulls ~500 MB)
make api &
make benchmark
```

Yêu cầu: Docker Desktop ≥ 4.x, RAM ≥ 8 GB free, port 6333/6380/5432 không xung đột (Redis lab dùng **6380** để không đụng Redis :6379 sẵn có trên máy).
Endpoints: Qdrant http://localhost:6333 · Redis **:6380** · Postgres :5432

---

## Cấu trúc & tiến trình

| Notebook | Skill | Slide deliverable | Pass when… |
|---|---|---|---|
| `01_embeddings_index` | Embed corpus với `fastembed` + index in Qdrant + similarity search | Bullet 1 — top-5 results trả về cho query VN | indexed = 1000 vectors; top-5 cho paraphrase query đúng cluster |
| `02_hybrid_search_rrf` | BM25 + vector + RRF (k=60) + đánh giá Precision@10 trên 50 golden queries | Bullet 2 — hybrid > keyword & semantic | Hybrid wins on `mixed` slice; thắng trung bình tổng thể |
| `03_search_api_benchmark` | FastAPI `/search?q=...&mode=...` + đo P50/P95/P99 latency | Bullet 1 + 4 — REST endpoint < 50ms P99 | Hybrid P99 server-side < 50 ms |
| `04_feast_feature_store` | 3 feature views + `feast apply` + `materialize` + online lookup + PIT join | Bullet 3 — Feast 3 views materialize+online | `materialize` thành công; online lookup P99 < 10ms |

**Source format:** Notebooks live as Jupytext `.py` files (small, easy to review).
`bash setup-lite.sh` and `make lab` auto-convert to `.ipynb`. Edit `.ipynb` in
Jupyter and Jupytext keeps both in sync.

---

## Deliverable (4 notebook đã chạy + ảnh chụp + reflection)

Mapping 1-to-1 với slide deliverable bullets:

1. **NB1** — Indexed 1000 vectors; top-5 results cho query Vietnamese; paraphrase query trả về đúng topic cluster.
2. **NB2** — Bảng Precision@10 với 3 mode (kw/sem/hyb), hybrid trung bình > 2 mode khác; bảng slice theo loại query (`exact`/`paraphrase`/`mixed`).
3. **NB3** — FastAPI `/search` response sample + bảng P50/P95/P99 cho 3 mode; hybrid P99 server-side < 50 ms.
4. **NB4** — `feast apply` thành công + `materialize` log + online lookup result + PIT join DataFrame.

Chấm điểm: xem [`rubric.md`](rubric.md). **Tổng 100 pts → Track-2 Daily Lab (30%)** + 20 pts bonus optional.

---

## Vibe-coding tips

Lab này được thiết kế cho **vibe-coding era** với CLI workflow: bạn dùng
AI assistant trong terminal (Claude Code, Codex CLI, OpenCode) để
generate boilerplate, focus vào *judgment decisions*. Đọc
[`VIBE-CODING.md`](VIBE-CODING.md) **trước khi bắt đầu NB1** (5–10 phút)
— file đó là general primer cover:

- Spec-Driven Development (SDD) và TDD trong LLM era
- Khi nào delegate cho AI, khi nào tự nghĩ
- 5 prompt patterns universal (specs in / validate before generate / TDD /
  minimal repro / plan-code-review)
- CLI tool recommendations (Claude Code / Codex CLI / OpenCode)
- 3 anti-patterns phổ biến

Mỗi notebook cũng có **vibe-coding callout** ở cuối: nói rõ subtask nào
trong notebook đó *nên* delegate cho AI, subtask nào *phải* bạn tự nghĩ.

---

## Bonus Challenge — Build Your Own AI Memory (optional, ungraded)

Một creative session 4–6 giờ: thiết kế và build minimal **AI assistant với
hybrid memory** kết hợp Vector Store (episodic memory) và Feature Store
(stable user profile). Vibe coding khuyến khích — code boilerplate AI lo,
*architecture decisions* bạn tự nghĩ + viết.

Format: brainstorm-first (15 phút sketching), code-second, làm đôi 2-3
học viên cũng được. Full brief + self-checklist:
[`BONUS-CHALLENGE.md`](BONUS-CHALLENGE.md) (tiếng Việt) ·
[`BONUS-CHALLENGE-EN.md`](BONUS-CHALLENGE-EN.md) (English).

---

## Cấu trúc repo

```
.
├── README.md                       # bạn đang đọc
├── VIBE-CODING.md                  # tips vibe-coding workflow
├── BONUS-CHALLENGE.md              # creative bonus brief (tiếng Việt)
├── BONUS-CHALLENGE-EN.md           # creative bonus brief (English)
├── rubric.md                       # 100-pt grading + 20 pt bonus
├── Makefile                        # dual-path orchestration
├── setup-lite.sh                   # lite path bootstrap (no Docker)
├── setup-docker.sh                 # docker path bootstrap (full stack)
├── docker-compose.yml              # Qdrant + Redis + Postgres
├── requirements.txt                # lite deps
├── requirements-full.txt           # docker extras
├── pyproject.toml                  # for `uv` users
├── .env.example                    # env template
├── notebooks/                      # 4 Jupytext .py files (source of truth)
│   ├── _setup.py
│   ├── 01_embeddings_index.py
│   ├── 02_hybrid_search_rrf.py
│   ├── 03_search_api_benchmark.py
│   └── 04_feast_feature_store.py
├── app/
│   ├── main.py                     # FastAPI /search endpoint
│   ├── search.py                   # Searcher class (kw / sem / hybrid)
│   └── feast_repo/
│       ├── feature_store.yaml      # Feast config (lite vs docker)
│       └── feature_views.py        # 3 feature views definition
├── scripts/
│   ├── seed_corpus.py              # 1000 VN docs + 50 golden queries (deterministic)
│   ├── benchmark.py                # Precision@10 + P99 latency harness
│   ├── verify_lite.py              # lite smoke test
│   └── verify_docker.py            # docker smoke test
├── data/                           # corpus + golden_set (regenerated by `make seed`)
└── submission/
    ├── REFLECTION.md               # template (≤ 200 words)
    └── screenshots/                # bạn add ảnh chụp ở đây
```

---

## Troubleshooting

| Triệu chứng | Fix |
|---|---|
| `setup-lite.sh` báo `python3: command not found` | Install Python 3.10+ (https://www.python.org/downloads/) |
| `make api` → port 8000 in use | `lsof -ti:8000 \| xargs kill -9` hoặc đổi `--port 8001` |
| NB1 báo `expected 1000 indexed, got X` | Chưa `make seed`; chạy lại |
| NB2 hybrid không thắng | Check RRF công thức: `1/(k + rank)` **rank 1-based**, không phải 0-based |
| NB3 P99 > 50ms | Bình thường ở cold start. Chạy 10 query warmup trước rồi đo lại. |
| NB4 `feast apply` lỗi | Xoá `app/feast_repo/registry.db` và chạy lại |
| Docker path: `port 6333 already allocated` | `docker compose down` rồi `docker compose up -d` |
| Docker path: Qdrant timeout | Đợi 60s sau `docker compose up`; image lần đầu pull ~200MB |

---

## Submission

**KHÔNG cần PR — chỉ submit GitHub URL công khai vào VinUni LMS.**

1. **Fork hoặc copy repo này lên GitHub account của bạn**, set repo **public**.
   ```bash
   # Hoặc tạo new repo trên github.com:
   git init -b main
   git remote add origin https://github.com/<your-username>/Day19-Track2-VectorFeatureStore-Lab.git
   ```
2. Hoàn thành 4 notebooks (giữ output cells trong `.ipynb`).
3. Add ảnh chụp vào `submission/screenshots/`:
   - NB1: Indexed 1000 vectors + top-5 paraphrase query
   - NB2: Bảng Precision@10 với hybrid > kw/sem
   - NB3: API response + bảng latency P50/P95/P99
   - NB4: `feast apply` STDOUT + online lookup result + PIT join DF
4. Điền `submission/REFLECTION.md` (≤ 200 chữ).
5. Push lên public repo:
   ```bash
   git add -A
   git commit -m "Lab 19 submission — <Họ Tên>"
   git push -u origin main
   ```
6. **Paste public GitHub URL của bạn vào ô submission của Day 19 trong VinUni LMS.** Không cần PR. Không cần fork-back.
7. (Optional) Bonus: thêm folder `bonus/` (xem `BONUS-CHALLENGE.md`) trước khi push.

> **Quan trọng:** Repo phải **public** đến khi điểm được công bố.
> Nếu private, grader không xem được → 0 điểm.

---

© VinUniversity AICB program · A20 cohort 2026 · Track 2 Day 19.
