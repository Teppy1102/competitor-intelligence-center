# LADIPAGE_DEPLOY_GUIDE.md — Deploy Frontend lên Ladipage

| | |
|---|---|
| **Thư mục nguồn** | `/ladipage` (`index.html`, `style.css`, `app.js`, `assets/`, `ladipage_embed.html`) |
| **Backend gọi tới** | `https://market-intelligence-center-api.onrender.com` (không đổi — đã production, đã bật CORS) |
| **Không đổi** | Backend, Endpoint, API, Report Logic, Prompt AI, Search Provider |
| **Đã test** | Chạy thật qua Internet với Backend Render (cả bản tách file và bản gộp `ladipage_embed.html`) — xem Mục 9 |

---

## ⚠️ CẢNH BÁO QUAN TRỌNG — Đọc trước khi làm bất cứ điều gì

Đã xảy ra thực tế trên `edu.linkpower.vn/research`: dùng **"Nhập từ HTML" / "Import from HTML"** khiến trang **không hoạt động** — giao diện bị bó cứng như mobile trên mọi màn hình, và nút Research **không gọi được API** (report không bao giờ xuất hiện). Nguyên nhân xác nhận bằng cách kiểm tra trực tiếp DOM của trang đã publish:

| Triệu chứng | Nguyên nhân thật (đã verify) |
|---|---|
| Giao diện luôn hẹp như mobile dù mở trên máy tính | "Nhập từ HTML" chuyển toàn bộ layout của mình thành các khối `ladi-section`/`ladi-box` có **width cố định bằng pixel** (vd `width: 420px; position: fixed`) — CSS responsive (media query) của `style.css` bị bỏ qua hoàn toàn. |
| Bấm Research không ra report | "Nhập từ HTML" **không giữ lại `app.js`** — kiểm tra `window.CONFIG` trên trang thật cho kết quả `undefined`, các `id` như `micKeywordInput`/`micResearchBtn` không tồn tại. Ladipage còn tự ý biến ô nhập + nút thành **1 form thu lead riêng** (`<form method="post" action=".../research">`) — bấm Research chỉ submit form nội bộ Ladipage, không liên quan gì tới API Render. |

**"Nhập từ HTML" (Import from HTML) và "HTML/Embed Code" (nhúng code) là 2 tính năng KHÁC NHAU HOÀN TOÀN của Ladipage:**

| | Nhập từ HTML *(SAI — đừng dùng)* | HTML/Embed Code *(ĐÚNG — cần dùng)* |
|---|---|---|
| Cách hoạt động | Đọc file HTML tĩnh rồi **vẽ lại thành trang kéo-thả** của Ladipage (giống import từ Figma) | **Nhúng nguyên khối** HTML/CSS/JS, giữ nguyên 100%, chạy độc lập như 1 trang web bình thường |
| CSS responsive (`@media`) | ❌ Bị bỏ qua, thay bằng vị trí/kích thước pixel cố định | ✅ Giữ nguyên, hoạt động đúng như đã test |
| JavaScript (`app.js`) | ❌ Không được giữ lại | ✅ Giữ nguyên, chạy đúng |
| Dùng khi nào | Khi muốn Ladipage **tự vẽ lại** design tĩnh để chỉnh sửa kéo-thả tiếp | Khi có sẵn 1 sản phẩm web hoàn chỉnh (như Market Intelligence Center) muốn nhúng y nguyên |

**→ Việc cần làm:** Xoá phần đã "Nhập từ HTML", tìm đúng phần tử **"HTML" / "Embed Code" / "Custom Code"** trong bảng chèn phần tử (Insert Element) của trình soạn thảo Ladipage (không phải ở bước tạo trang mới), kéo thả vào trang, rồi làm theo Bước 1–8 bên dưới. Nếu không tìm thấy phần tử này trong gói Ladipage đang dùng, liên hệ hỗ trợ Ladipage hỏi cụ thể tên gọi hiện tại của widget "nhúng HTML tuỳ chỉnh" — tôi không có quyền truy cập tài khoản Ladipage của bạn nên không thể tự thao tác thay.

---

## Mục 0 — Audit Frontend hiện tại

| Loại | Đang dùng | Ghi chú |
|---|---|---|
| HTML | `index.html` (1 file, chia 5 thành phần rõ ràng bằng comment: HERO, SEARCH, LOADING, DASHBOARD, FOOTER) | Không dùng template engine, không React/Vue |
| CSS | `style.css` (1 file, ~19KB) | Thuần CSS3 (custom properties, grid, flexbox), không Tailwind/Bootstrap CDN |
| JS | `app.js` (1 file, ~30KB) | Vanilla JS (ES6+), module hoá bằng IIFE — không React/Vue, không build step |
| Font | **Không dùng font ngoài** | Dùng system font stack (`-apple-system, Segoe UI, Roboto...`) — không gọi Google Fonts/CDN nào |
| SVG / Icon | Toàn bộ icon là **inline SVG** trong `app.js` (object `ICONS`) | Không dùng icon font (FontAwesome...), không request mạng ngoài cho icon |
| Asset | `assets/favicon.svg` | Duy nhất 1 asset ngoài — file rất nhỏ (278 byte) |
| Gọi mạng ngoài | Chỉ gọi `CONFIG.API_BASE` (Render API) | Không có `localhost`, không có CDN, không có font/analytics ngoài nào khác (đã grep xác nhận) |

**Kết luận audit:** Frontend hiện tại 100% tự chứa (self-contained) — chỉ phụ thuộc duy nhất 1 kết nối mạng ra ngoài là gọi API Backend. Điều này giúp việc đưa lên Ladipage đơn giản: không cần host CDN, không cần cấu hình font, không rủi ro conflict với theme/style sẵn có của Ladipage (mọi class CSS đều có tiền tố `mic-` để tránh trùng tên).

---

## Mục 1 — Phân chia thành phần (Component)

| Thành phần | Vai trò | Vị trí trong `index.html` |
|---|---|---|
| **Section Hero** | Tiêu đề, mô tả sản phẩm | `<!-- SECTION: HERO -->` |
| **Section Search** | Ô nhập từ khoá + nút Research + gợi ý ví dụ | `<!-- SECTION: SEARCH -->` |
| **Section Loading** | Vòng xoay + progress 5 bước + polling | `<!-- SECTION: LOADING -->` |
| **Section Dashboard** | 12 khối báo cáo, render từ JSON API | `<!-- SECTION: DASHBOARD -->` |
| **Footer** | Bản quyền + thời gian truy cập | `<!-- SECTION: FOOTER -->` |

Hero + Search nằm chung 1 khối hiển thị/ẩn (`#micViewHome`) vì luôn xuất hiện cùng lúc ở Trang chủ — Loading và Dashboard là 2 khối độc lập, JS chuyển đổi qua lại (`App.showView()`), không có framework/router nào can thiệp.

---

## Mục 2 — 2 phương án đưa vào Ladipage

Ladipage có 2 kiểu editor phổ biến cho khối code tự do:

- **Phương án A — Ladipage cho nhiều Block/nhiều tab (HTML / CSS / JS riêng):** dùng 3 file gốc `index.html`, `style.css`, `app.js` — làm theo Bước 1–8 bên dưới.
- **Phương án B — Ladipage chỉ có 1 ô HTML Block duy nhất:** dùng thẳng file **`ladipage_embed.html`** (đã gộp sẵn CSS + JS + favicon vào 1 file, không cần thao tác gì thêm) — dán nguyên file này vào ô HTML Block rồi qua thẳng Bước 6 (Publish).

`ladipage_embed.html` được sinh tự động từ đúng 3 file gốc (không viết tay riêng, không có logic/giao diện khác biệt) — nếu cần sửa giao diện/logic, luôn sửa ở `index.html`/`style.css`/`app.js` rồi tạo lại `ladipage_embed.html`, không sửa trực tiếp file gộp.

---

## Bước 1 — Tạo Landing Page

1. Đăng nhập Ladipage.
2. Tạo **Landing Page mới** (trắng/blank) hoặc chọn trang có sẵn muốn gắn Market Intelligence Center vào.
3. Đặt tên trang, ví dụ: `Market Intelligence Center`.

## Bước 2 — Tạo HTML Block

4. Trong trình soạn thảo trang, kéo thả element **"HTML Code" / "Embed Code" / "Custom Code"** vào vị trí muốn hiển thị công cụ.
5. Xác định editor thuộc **Phương án A** (có tab HTML/CSS/JS riêng) hay **Phương án B** (chỉ 1 ô) — xem Mục 2.

## Bước 3 — Copy HTML

6. **Phương án A:** copy toàn bộ nội dung `index.html`, dán vào tab **HTML**.
7. **Phương án B:** copy toàn bộ nội dung `ladipage_embed.html`, dán thẳng vào ô HTML Block duy nhất — **bỏ qua Bước 4 và Bước 5**, chuyển thẳng tới Bước 6.

## Bước 4 — Copy CSS *(chỉ Phương án A)*

8. Copy toàn bộ nội dung `style.css`, dán vào tab **CSS**.

## Bước 5 — Copy JS *(chỉ Phương án A)*

9. Copy toàn bộ nội dung `app.js`, dán vào tab **JS**.
10. Kiểm tra dòng đầu file `app.js`:
    ```js
    API_BASE: "https://market-intelligence-center-api.onrender.com",
    ```
    Đây là **dòng duy nhất** cần sửa nếu sau này Backend đổi domain — hiện tại giữ nguyên, không sửa gì.

## Bước 6 — Publish

11. Lưu (Save) khối HTML Block vừa cấu hình.
12. Bấm **Preview/Xem trước** toàn trang Ladipage — kiểm tra nhanh Trang chủ hiển thị đúng (Hero + ô nhập từ khoá + nút Research + gợi ý ví dụ).
13. Bấm **Publish/Xuất bản** trang.

## Bước 7 — Test

14. Mở URL trang Ladipage **đã publish** (không phải chỉ bản Preview nội bộ — trình duyệt thật xử lý mạng/CORS khác với chế độ xem trước).
15. Nhập 1 từ khoá thật (ví dụ **"Khóa học OKR"**), bấm **Research**.
16. Quan sát màn hình Loading chạy đúng animation + 5 bước tiến trình.
17. Đợi khoảng 60–130 giây — Dashboard phải tự hiển thị, không cần bấm gì thêm.
18. Kiểm tra đủ 12 khối trong Dashboard (xem Bước 8 — Checklist).
19. Bấm **Download HTML** — xác nhận trình duyệt tải về 1 file `.html` chứa report đầy đủ, mở được độc lập.
20. Bấm **Research Again** — xác nhận quay lại đúng Trang chủ, ô nhập từ khoá được reset trống.

## Bước 8 — Checklist

Dùng checklist này để xác nhận **chỉ cần copy/paste là chạy đúng**, không cần đọc lại code:

**Cấu hình**
- [ ] Đã chọn đúng Phương án A hoặc B theo editor Ladipage đang dùng (Mục 2).
- [ ] Không có dòng nào trong code còn chứa `localhost` (đã audit — không có).
- [ ] `API_BASE` trỏ đúng `https://market-intelligence-center-api.onrender.com`.

**Trang chủ**
- [ ] Hero + tiêu đề + mô tả hiển thị đúng.
- [ ] Ô nhập từ khoá + nút Research hoạt động.
- [ ] Bấm 1 chip ví dụ (vd "Khóa học HRBP") tự điền vào ô nhập.

**Loading**
- [ ] Vòng xoay (orb) chạy animation mượt.
- [ ] Danh sách 5 bước tiến trình chuyển trạng thái theo thời gian thực (không đứng yên 1 chỗ).
- [ ] Nếu API lỗi, hiển thị đúng thông báo lỗi + nút "Quay lại trang chủ".

**Dashboard — đủ 12 khối, dữ liệu đọc từ JSON thật**
- [ ] Executive Dashboard (10 câu hỏi)
- [ ] KPI Cards (7 Score: Competition, Opportunity, Trend, Authority, Content Saturation, SEO Difficulty, AI Confidence)
- [ ] Market Overview
- [ ] Top Websites
- [ ] Competitor
- [ ] Key Messages
- [ ] Trend
- [ ] Gap
- [ ] Opportunity
- [ ] Benchmark
- [ ] Recommendation
- [ ] Action Plan
- [ ] Sources
- [ ] Footer (bản quyền + thời gian truy cập)

**Hành động**
- [ ] Download HTML tải file thành công, mở ra xem đúng nội dung report.
- [ ] Research Again quay lại đúng Trang chủ, không còn dữ liệu report cũ sót lại.

**Responsive**
- [ ] Desktop (≥1024px): layout 2 cột cho các khối Dashboard, KPI grid nhiều cột.
- [ ] Tablet (~768px): layout co về 1–2 cột, không tràn ngang, không chữ bị cắt.
- [ ] Mobile (~375px): mọi khối xếp dọc 1 cột, nút bấm đủ lớn để chạm.

---

## Mục 9 — Đã test thật (không chỉ đọc code)

- Chạy `/ladipage` qua local static server (không phải `file://`), gọi thẳng Backend Render qua Internet (cross-origin thật, CORS thật).
- Test **cả 2 phương án**: bản tách file (`index.html` + `style.css` + `app.js`) và bản gộp (`ladipage_embed.html`) — cả hai cho kết quả **giống hệt nhau**, cùng 1 pipeline JS, không có logic riêng cho từng bản.
- Full flow thật với từ khoá thật ("Khóa học HRM", "Khóa học BSC-KPI"): Research → Loading (stage animation theo thời gian thực) → Dashboard hiển thị đủ 12 khối với dữ liệu JSON thật từ Render → Download HTML không lỗi → Research Again reset đúng.
- Responsive: kiểm tra ở **Desktop, Tablet (768px), Mobile (375px)** — không vỡ layout ở độ rộng nào.
- 0 lỗi console trong toàn bộ quá trình test.

---

## Mục 10 — Giới hạn cần biết

- 1 lượt Research mất khoảng 60–130 giây (1 lần gọi AI duy nhất) — đã có Loading animation phù hợp, không cần xử lý gì thêm.
- Không có Database ở Backend — Frontend này không hiển thị lịch sử các lần Research trước (đúng phạm vi flow đã thống nhất).
- Nếu Backend Render ở gói Free "ngủ" do không có traffic, lượt Research đầu tiên có thể chậm hơn bình thường (cold start) — không phải lỗi Frontend, không cần sửa gì.
