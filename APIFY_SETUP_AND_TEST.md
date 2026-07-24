# APIFY_SETUP_AND_TEST.md — Cấu hình & kiểm thử Facebook Provider (Apify)

> Áp dụng từ Sprint bổ sung "Chuyển Facebook Provider sang Apify". Facebook Provider
> production **mặc định** là Apify (không còn Playwright — xem `providers/registry.py`).

---

## 1. Kiểm tra file `.env`

File `.env` (KHÔNG được commit — đã có trong `.gitignore`: `.env`, `.env.*`,
trừ `.env.example`) cần có tối thiểu:

```
OPENAI_API_KEY=...
FACEBOOK_PROVIDER=apify
APIFY_API_TOKEN=...
```

Kiểm tra nhanh **không làm lộ giá trị token** (PowerShell hoặc Git Bash):

```bash
sed -E 's/=.*/=<redacted>/' .env
```

Lệnh trên chỉ in **tên biến**, che toàn bộ giá trị — dùng lệnh này thay vì
`cat .env` mỗi khi cần xác nhận biến nào đã có mà không cần nhìn thấy giá trị thật.

Nếu thiếu `APIFY_API_TOKEN`, `main.py` sẽ trả lỗi rõ ràng (HTTP 500, message
chứa đúng tên biến, không phải crash không rõ nguyên nhân) — xem
`providers/registry.py::_build_apify_extractor()`.

## 2. Lấy APIFY_API_TOKEN

1. Đăng nhập [console.apify.com](https://console.apify.com).
2. Vào **Settings → Integrations**.
3. Copy **Personal API token**.
4. Dán vào `.env`: `APIFY_API_TOKEN=<token>` — **không dán vào bất kỳ file nào khác**
   (source code, config.json, README, test fixture đều bị cấm — xem quy tắc ở đầu
   phiên làm việc đã thống nhất).

## 3. Chạy smoke test thật

```bash
python scripts/smoke_test_apify.py https://www.facebook.com/LinkPowerVN
```

Mặc định script chỉ lấy **tối đa 5 bài** để tiết kiệm credit Apify (đổi bằng
`--max-posts N`, tối đa vẫn bị hard-cap ở 30). Script:

- Đọc `APIFY_API_TOKEN` từ `.env` — **không bao giờ in giá trị token** ra terminal.
- Gọi cả Pages Scraper và Posts Scraper (song song, đúng 1 run mỗi loại).
- In số record Page/Post, tên field chính, số bài sau normalize, trạng thái
  `ok` / `partial_data` / `data_unavailable`.
- **Không** tự chạy trong unit test/CI — chỉ chạy tay khi cần xác nhận thực tế.

## 4. Cách đọc Dataset (khi cần debug thủ công trên Apify Console)

1. Vào **Actors → Runs** trên console.apify.com, tìm run vừa tạo bởi
   `apify/facebook-pages-scraper` hoặc `apify/facebook-posts-scraper`.
2. Tab **Output** → xem toàn bộ item dạng JSON.
3. Đối chiếu tên field thật với danh sách candidate key trong
   `providers/facebook_apify_provider.py` (`_first_present(item, "title", "pageName", "name")`
   và các hàm `_map_profile()`/`_map_post()`) — nếu Actor đổi cấu trúc, **chỉ cần
   thêm tên field mới vào danh sách candidate**, không cần sửa logic khác.

> **Lưu ý quan trọng:** Tên field trong tài liệu này (`title`, `categories`,
> `likes`, `followers`, `postId`, `time`, `reactions`...) là suy đoán tốt nhất
> dựa trên hiểu biết chung về 2 Actor này tại thời điểm viết code — **chưa
> được xác nhận bằng 1 lần gọi API thật** (không có token khi thực hiện
> phiên làm việc này). Bắt buộc chạy `scripts/smoke_test_apify.py` với token
> thật **trước khi coi tính năng là production-ready**, và cập nhật lại danh
> sách candidate key trong `facebook_apify_provider.py` nếu tên field thực tế
> khác với suy đoán.

## 5. Cách xem chi phí (cost) của 1 Actor run

- Console Apify: **Actors → Runs → chọn run → tab Info** → mục *Usage*.
- Trong log ứng dụng (`cic.facebook_apify` logger), mỗi run đã hoàn tất được
  ghi: `apify_run_finished label=... actor=... run_id=... status=... duration_s=... usage_usd=...`
  — không cần vào Console nếu chỉ cần xem nhanh log Render.

## 6. Thêm biến môi trường lên Render

Vào Render Dashboard → service → **Environment** → thêm (giá trị token nhập
tay trực tiếp trên Render, **không** upload file `.env`):

| Biến | Giá trị |
|---|---|
| `APIFY_API_TOKEN` | *(dán token thật, đánh dấu Secret)* |
| `FACEBOOK_PROVIDER` | `apify` |
| `APIFY_FACEBOOK_PAGES_ACTOR` | `apify/facebook-pages-scraper` |
| `APIFY_FACEBOOK_POSTS_ACTOR` | `apify/facebook-posts-scraper` |
| `APIFY_MAX_POSTS` | `30` |
| `APIFY_TIMEOUT_SECONDS` | `180` |

`render.yaml` đã khai báo sẵn các biến này (trừ giá trị thật của
`APIFY_API_TOKEN`, đánh dấu `sync: false` — Render sẽ yêu cầu nhập tay trên
Dashboard, không tự sinh giá trị).

**Tuyệt đối không** commit file `.env` hoặc dán token vào bất kỳ file nào
trong repo rồi push lên Render qua git — chỉ nhập trực tiếp trên giao diện
Render.

## 7. Chuyển thủ công về Playwright (nếu cần)

Chỉ nên dùng khi Apify tạm thời gặp sự cố hoặc hết credit và cần chạy demo
gấp — **không phải fallback tự động**:

```bash
# Trên Render: đổi biến môi trường FACEBOOK_PROVIDER = playwright
# Cục bộ: thêm vào .env
FACEBOOK_PROVIDER=playwright
```

Khi đó `providers/registry.py` sẽ import `PlaywrightFacebookExtractor` (lazy
import — chỉ xảy ra khi biến này được đặt). Cần cài thêm:

```bash
pip install -r requirements-dev.txt
playwright install chromium
```

Và cân nhắc lại RAM (xem `DEPLOY_MVP_FACEBOOK.md` mục Rollback).

## 8. Kiểm tra 30 bài gần nhất

- `providers/facebook_apify_provider.py::FACEBOOK_POST_LIMIT = 30` — hard cap,
  không phụ thuộc cấu hình.
- Test tự động: `tests/test_providers/test_facebook_apify_provider.py`
  (`test_posts_more_than_30_capped_to_30_newest`,
  `test_posts_fewer_than_30_uses_all_actual_and_status_partial`).
- Kiểm tra thủ công: chạy smoke test với `--max-posts 30` trên 1 Fanpage hoạt
  động mạnh, xác nhận `len(result.posts) <= 30` và log
  `apify_dataset_read ... item_count=...`.

## 9. Kiểm tra frontend không còn bộ chọn tháng

```bash
python -m pytest tests/test_frontend/ -v
```

Bộ test này đọc trực tiếp `ladipage/index.html`/`app.js` và xác nhận: không
còn `1_month`/`3_months`/`6_months`/`<select>` trong section Competitor
Intelligence, không có chuỗi `time_range` trong `app.js`, có dòng mô tả "tối
đa 30 bài viết gần nhất".

## 10. Xác nhận hệ thống không bịa dữ liệu

- Chạy `python -m pytest tests/ -v` — các test `test_both_actors_failed_status_unavailable`,
  `test_pages_success_posts_failed_status_partial_profile_kept`,
  `test_posts_success_pages_failed_status_partial_posts_kept` xác nhận 4
  trường hợp A/B/C/D đều trả đúng trạng thái, không tạo số liệu thay thế.
- Audit thủ công: chạy smoke test với 1 Fanpage ít hoạt động, xác nhận
  `data_status` trả về `partial`/`insufficient` (không phải `complete`) khi số
  bài thu được ít hơn 30, và `report_json["posts_analyzed"]` khớp đúng số bài
  thật (không phải luôn là 30).

## 11. Cách rollback nếu Apify gặp lỗi

1. **Sự cố tạm thời (Apify downtime/rate limit):** không cần rollback code —
   endpoint đã trả lỗi rõ ràng (`data_unavailable`/`partial_data`), người
   dùng thấy thông báo, thử lại sau.
2. **Cần chạy demo ngay trong lúc Apify lỗi:** đặt tạm
   `FACEBOOK_PROVIDER=playwright` trên Render (xem mục 7) — chấp nhận dữ liệu
   hạn chế hơn (thường chỉ ~1 bài do Facebook giới hạn xem ẩn danh).
3. **Cần rollback code (vd bản deploy mới lỗi):** dùng tính năng **Rollback**
   trên Render Dashboard (chọn deploy trước đó) — không cần thao tác Git đặc biệt.
