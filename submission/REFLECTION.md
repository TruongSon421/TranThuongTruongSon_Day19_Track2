# Reflection — Lab 19

**Tên:** Trần Thương Trường Sơn
**Cohort:** Track 2
**Path đã chạy:** docker

---

## Câu hỏi (≤ 200 chữ)

> Trên golden set 50 queries, mode nào thắng ở loại query nào (`exact` /
> `paraphrase` / `mixed`), và tại sao? Khi nào bạn **không** dùng hybrid
> (i.e. khi nào pure BM25 hoặc pure vector là lựa chọn đúng)?

BM25 thắng trên **exact** queries vì nó match token chính xác — khi user gõ đúng từ khóa kỹ thuật ("Kubernetes", "RBAC"), TF-IDF reward term frequency trực tiếp. Semantic search bị "diluted" vì embedding của query ngắn ít context.

Vector thắng trên **paraphrase** queries — khi user nói "tự động mở rộng hạ tầng" thay vì "auto-scaling", cosine similarity trong embedding space capture nghĩa dù không có token overlap. BM25 hoàn toàn miss những case này.

Hybrid (RRF) thắng trên **mixed** queries vì kết hợp được điểm mạnh của cả hai: exact match từ BM25 + semantic coverage từ vector.

**Khi không dùng hybrid:** (1) Latency budget cực thấp (<5ms) — 2 retrievers song song vẫn tốn overhead; dùng pure BM25 nếu domain có vocabulary cố định. (2) Corpus rất nhỏ (<1000 docs) — BM25 đã đủ, không cần embedding overhead. (3) Structured keyword search (product code, ID) — semantic search không thêm giá trị.

---

## Điều ngạc nhiên nhất khi làm lab này

Feast `PostgreSQLSource` và `FileSource` không tương thích trong cùng một registry — chuyển offline store từ file sang postgres đòi hỏi xóa `registry.db` và đồng bộ Parquet → Postgres trước khi `feast apply`. Đây là điểm dễ bị bỏ qua khi chuyển từ lite path sang docker path.

---

## Bonus challenge

- [x] Đã làm bonus (xem `bonus/`)

