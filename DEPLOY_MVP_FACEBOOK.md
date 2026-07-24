# DEPLOY_MVP_FACEBOOK.md — Deploy Competitor Intelligence Center (Facebook MVP, Apify)

> Cập nhật sau khi chuyển Facebook Provider sang Apify. Không tự động deploy được
> trong phiên làm việc này (không có quyền truy cập tài khoản Render/Ladipage của
> bạn) — tài liệu này liệt kê CHÍNH XÁC các bước cần làm thủ công.

---

## 1. Cấu hình Render

| Mục | Giá trị |
|---|---|
| **Root Directory** | `COMPETITOR_INTELLIGENCE_CENTER` (thư mục con trong repo, nếu repo gộp chung nhiều module) |
| **Build Command** | `pip install -r requirements.txt` (KHÔNG còn `playwright install --with-deps chromium` — Apify không cần Chromium) |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path** | `/api/health` |
| **Plan đề xuất** | `free` (512MB RAM đủ dùng — không còn chạy headless browser); chỉ cần nâng cấp nếu chủ động dùng lại Playwright |

`render.yaml` trong thư mục này đã khai báo đầy đủ — nếu dùng tính năng
"Blueprint" của Render, chỉ cần trỏ vào file này.

## 2. Biến môi trường bắt buộc trên Render

Vào **Environment** trên Render Dashboard, thêm (không upload `.env`):

```
OPENAI_API_KEY=<nhập tay, đánh dấu Secret>
OPENAI_MODEL=gpt-5-mini
FACEBOOK_PROVIDER=apify
APIFY_API_TOKEN=<nhập tay, đánh dấu Secret>
APIFY_FACEBOOK_PAGES_ACTOR=apify/facebook-pages-scraper
APIFY_FACEBOOK_POSTS_ACTOR=apify/facebook-posts-scraper
APIFY_MAX_POSTS=30
APIFY_TIMEOUT_SECONDS=180
```

Xem chi tiết cách lấy `APIFY_API_TOKEN` ở `APIFY_SETUP_AND_TEST.md`.

## 3. Repo Git

`COMPETITOR_INTELLIGENCE_CENTER/` **chưa có git repo riêng** tại thời điểm
viết tài liệu này. Cần:

```bash
cd COMPETITOR_INTELLIGENCE_CENTER
git init
git add .   # kiểm tra `git status` trước — .env phải KHÔNG xuất hiện trong danh sách
git commit -m "Facebook MVP - Apify provider"
git remote add origin <URL repo GitHub của bạn>
git push -u origin main
```

Sau đó kết nối repo này với Render (New Web Service → Connect a repository).

## 4. Frontend Ladipage

File cuối cùng cần dán vào Ladipage: **`ladipage/ladipage_embed.html`**
(bản gộp sẵn CSS + JS + favicon, dán thẳng vào khối "HTML/Embed Code" —
**không dùng "Nhập từ HTML"**, xem cảnh báo chi tiết ở `ladipage/LADIPAGE_DEPLOY_GUIDE.md`).

Trước khi dán, xác nhận dòng `API_BASE` trong `ladipage/app.js` (module `Cic`)
đã trỏ đúng domain Render thật:

```js
const CONFIG = Object.freeze({
  API_BASE: "https://competitor-intelligence-center-api.onrender.com",
  ...
```

Nếu domain Render khác (Render tự sinh tên nếu không đặt tay khớp
`render.yaml`), sửa đúng 1 dòng này trong `app.js`, sau đó **chạy lại script
gộp** để cập nhật `ladipage_embed.html` (xem `ladipage/LADIPAGE_DEPLOY_GUIDE.md`
mục "2 phương án đưa vào Ladipage").

## 5. Kiểm tra sau deploy

1. Mở `https://<domain-render>/api/health` — phải trả `{"status":"ok",...}`.
2. Test 1 request thật (thay domain thật):
   ```bash
   curl -X POST https://<domain-render>/api/competitor/facebook \
     -H "Content-Type: application/json" \
     -d '{"url":"https://www.facebook.com/LinkPowerVN"}'
   ```
3. Mở trang Ladipage đã publish, dán 1 URL Fanpage thật, bấm "Phân tích",
   xác nhận: hiển thị đúng số bài thật đã thu thập, nhãn trạng thái dữ liệu
   (Đầy đủ/Một phần/Không đủ dữ liệu), không có màn hình trắng khi lỗi.

## 6. Rollback

- **Rollback code:** Render Dashboard → service → **Deploys** → chọn bản
  deploy trước đó → **Rollback to this deploy**.
- **Rollback provider (Apify → Playwright tạm thời):** xem
  `APIFY_SETUP_AND_TEST.md` mục 11 — chỉ đổi biến môi trường
  `FACEBOOK_PROVIDER`, không cần deploy lại code, nhưng cần thêm bước cài
  Playwright/Chromium vào build (xem cảnh báo RAM ở mục 1).

## 7. Có còn cần Chromium trên production không?

**Không.** Facebook Provider mặc định (Apify) không dùng Chromium/Playwright.
Playwright vẫn còn trong source code (`providers/facebook_playwright_provider.py`)
làm lựa chọn dự phòng thủ công, nhưng build production tiêu chuẩn
(`requirements.txt` + `render.yaml` hiện tại) **không cài Playwright/Chromium**,
giúp build nhanh hơn và dùng ít RAM hơn đáng kể so với thiết kế trước đó.
