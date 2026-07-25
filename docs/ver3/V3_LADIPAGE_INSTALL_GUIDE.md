# V3_LADIPAGE_INSTALL_GUIDE.md — Cài Social Competitor Benchmark lên Ladipage

> Sprint V3.3.3. File cần dùng: [`dist/ladipage/ver3-social-benchmark-embed.html`](../../dist/ladipage/ver3-social-benchmark-embed.html)
> (bản đọc được, để sửa sau này) hoặc
> [`dist/ladipage/ver3-social-benchmark-embed.min.html`](../../dist/ladipage/ver3-social-benchmark-embed.min.html)
> (bản rút gọn ~36%, nội dung/hành vi giống hệt bản gốc — dùng bản nào cũng
> được, khuyến nghị dùng bản `.min.html` khi dán vào Ladipage để nhẹ trang hơn).

Đây là widget **riêng cho module Social Competitor Benchmark (Ver 3)** —
KHÁC với `ladipage/ladipage_embed.html` (Market Intelligence Center +
Competitor Intelligence Center Facebook MVP của Ver 1/Ver 2). Có thể dán cả
2 widget vào cùng 1 trang Ladipage nếu muốn — chúng độc lập hoàn toàn
(namespace CSS/JS riêng, không dùng chung state).

## 1. Trước khi làm — đọc cảnh báo quan trọng

Áp dụng **NGUYÊN VĂN** cảnh báo đã có ở
[`ladipage/LADIPAGE_DEPLOY_GUIDE.md`](../../ladipage/LADIPAGE_DEPLOY_GUIDE.md)
mục "⚠️ CẢNH BÁO QUAN TRỌNG": Ladipage có 2 tính năng dễ nhầm —

| | "Nhập từ HTML" *(SAI — đừng dùng)* | "HTML / Embed Code / Custom Code" *(ĐÚNG)* |
|---|---|---|
| Cách hoạt động | Vẽ lại thành block kéo-thả, **bỏ CSS responsive + toàn bộ JS** | Nhúng nguyên khối, chạy như 1 trang web bình thường |
| Dùng cho file này | ❌ Sẽ hỏng — mất `<style>`/`<script>` | ✅ Bắt buộc dùng đúng phần tử này |

Tìm phần tử **"HTML" / "Embed Code" / "Custom Code"** trong bảng chèn phần
tử (Insert Element) của trình soạn thảo Ladipage — không phải bước "Nhập từ
HTML" khi tạo trang.

## 2. Nội dung file (đối chiếu yêu cầu bảo mật)

- 1 file HTML duy nhất, tự chứa toàn bộ CSS (`<style>`) + JS (`<script>`) —
  không có `<link>`/`<script src>` trỏ ra ngoài, không gọi CDN/font ngoài.
- **Không chứa secret nào** — không có Apify token, OpenAI key, database
  credential, hay bất kỳ chuỗi bí mật nào. Trình duyệt **chỉ gọi Backend
  API** (`/api/v3/benchmark/*`) — không bao giờ gọi thẳng Apify/OpenAI.
- Toàn bộ CSS dùng tiền tố `lpv3-`, mọi rule đều nằm dưới `#lpv3-root` —
  không sửa CSS toàn cục của Ladipage (đã tự kiểm chứng bằng cách nhúng vào
  1 trang giả lập có CSS toàn cục cố tình xung đột — xem
  `docs/ver3/V3_SPRINT_033_REPORT.md` mục E).
- Toàn bộ JS nằm trong 1 IIFE duy nhất — không tạo biến global nào (đã kiểm
  tra `window` sau khi chạy, 0 biến rò rỉ).
- Chỉ 1 gốc DOM duy nhất `<div id="lpv3-root">` — không dùng ID nào khác có
  nguy cơ trùng với phần còn lại của trang.

## 3. Các bước dán vào Ladipage (tối đa 10 bước)

1. Đăng nhập Ladipage, mở trang muốn gắn Social Competitor Benchmark vào
   (trang mới hoặc trang có sẵn).
2. Trong trình soạn thảo, kéo thả phần tử **"HTML" / "Embed Code" / "Custom
   Code"** vào vị trí muốn hiển thị (xem cảnh báo Mục 1).
3. Mở file `dist/ladipage/ver3-social-benchmark-embed.min.html`, copy
   **toàn bộ nội dung file**.
4. Dán nguyên văn vào ô HTML Block vừa tạo — không sửa gì thêm.
5. (Tuỳ chọn) Nếu Backend API đổi domain sau này, sửa **duy nhất 1 chỗ**:
   giá trị mặc định của ô input Backend API ở khối "Cấu hình" đầu widget —
   xem Mục 4 bên dưới, không cần sửa gì trong JS.
6. Lưu (Save) khối HTML Block.
7. Bấm **Preview/Xem trước** — kiểm tra khối "Backend API" hiện "Kết nối
   OK" (màu xanh) sau khi bấm "Kiểm tra kết nối".
8. Thử tạo 1 dự án test (Bước 1 trên widget) để chắc chắn gọi API thành
   công trên bản Preview.
9. Bấm **Publish/Xuất bản** trang.
10. Mở URL đã publish (không phải chỉ bản Preview nội bộ) và lặp lại Mục 5
    của Checklist test (xem Mục 6 bên dưới).

## 4. Khối "Cấu hình" — nơi DUY NHẤT cần biết

Ngay đầu widget có 1 khối nền tối "Backend API" với:

- 1 ô nhập URL Backend — **đã điền sẵn** giá trị production thật
  `https://competitor-intelligence-center-api.onrender.com` (đây là domain
  đã dùng chung cho toàn bộ API Ver 2/Ver 3, xem
  `docs/ver3/V3_API_DOCUMENTATION.md`).
- Nút "Kiểm tra kết nối" — gọi `GET /api/v3/health`, hiện chấm xanh/đỏ.
- Giá trị người dùng tự sửa (nếu có) được lưu vào `localStorage` của trình
  duyệt (**không phải secret** — chỉ là 1 URL công khai) để lần sau mở lại
  không cần nhập lại.

Không có nơi nào khác trong file cần sửa để đổi Backend — mọi lệnh gọi API
trong JS đều đọc lại giá trị này.

## 5. Widget làm được gì

- Bước 1 — Tạo dự án Benchmark (tên, mục tiêu, khoảng ngày, số bài tối đa).
- Bước 2 — Thêm LinkPower + nhiều đối thủ (brand), mỗi brand thêm nhiều
  kênh Facebook/LinkedIn/TikTok (nhận diện nền tảng tự động từ URL).
- Bước 3 — Chạy Benchmark: hiện tiến trình **theo từng kênh** (poll
  `GET /jobs` mỗi 3s trong lúc chờ, tự dừng khi xong hoặc sau tối đa ~10
  phút — không bao giờ chờ vô hạn), có nút "Huỷ chờ" ở phía trình duyệt,
  nút "Thử lại kênh này" cho từng kênh lỗi.
- Manual Import — kênh ở trạng thái "Cần nhập thủ công"/"Thất bại" có nút
  mở panel upload `.csv`/`.json`, xem trước dữ liệu (preview) trước khi xác
  nhận nhập, sau đó bấm "Thử lại kênh này" để tính lại benchmark.
- Bước 4 — Report đầy đủ 10 mục A–J + dropdown "Lịch sử report" xem lại các
  phiên bản trước.
- Xử lý lỗi rõ ràng cho: API offline/URL Backend sai, quá thời gian chờ,
  URL kênh sai định dạng, cần nhập thủ công, rate limit (429), dự án đang
  chạy dở (409, "1 dự án 1 lượt chạy tại 1 thời điểm").

## 6. Test nhanh sau khi Publish (tối đa 5 bước)

1. Mở URL trang đã Publish (trình duyệt thật, không phải Preview nội bộ).
2. Bấm "Kiểm tra kết nối" — phải hiện "Kết nối OK".
3. Tạo 1 dự án test, thêm 1 brand LinkPower + 1 kênh Facebook/LinkedIn/TikTok
   thật, bấm "Chạy Benchmark" — quan sát trạng thái từng kênh cập nhật
   trong lúc chờ (không đứng yên/không báo lỗi ngay).
4. Sau khi chạy xong, cuộn xuống Report — xác nhận đủ 10 mục A–J hiển thị
   (mục nào chưa đủ dữ liệu sẽ ghi rõ "Không đủ dữ liệu", không bịa số).
5. Thử trên điện thoại thật (hoặc thu nhỏ trình duyệt xuống ~375px) — xác
   nhận không bị tràn ngang, các khối xếp dọc 1 cột.

## 7. Giới hạn cần biết (không phải lỗi của widget)

> **Cập nhật Sprint V3.3.4:** 3 mục dưới đây (CORS PUT/DELETE, Idempotency-Key,
> `partially_completed`) đã được SỬA — xem `docs/ver3/V3_SPRINT_034_FINAL_REPORT.md`.
> Giữ lại đoạn mô tả cũ bên dưới để biết hành vi TRƯỚC Sprint V3.3.4 (tham
> khảo lịch sử), hành vi HIỆN TẠI xem `docs/ver3/V3_PRODUCTION_ENV_GUIDE.md`.

1. ~~CORS Backend hiện tại chỉ cho phép GET/POST/OPTIONS~~ — **đã mở
   PUT/DELETE** (`main.py:_parse_allowed_origins()`), cấu hình qua
   `ALLOWED_ORIGINS` (mặc định chỉ `https://edu.linkpower.vn`, không
   wildcard `*`).
2. ~~Không có Idempotency-Key header~~ — **đã có**, widget gửi 1 UUID mới
   mỗi lần bấm nút cho 4 POST quan trọng (tạo dự án, chạy benchmark, retry
   job, import) — xem `v3/services/idempotency_service.py`. 2 lớp chống bấm
   trùng cũ (disable nút, `409 DuplicateRunError`) vẫn giữ nguyên, hoạt động
   song song, không thay thế nhau.
3. ~~`project.status` không bao giờ là `"partially_completed"`~~ — **đã có**,
   backend tự tính (`pipeline_service._derive_project_status()`) và trả qua
   `project.status`, response `/run`/`/retry`, và `full_report.status`.
   Widget ưu tiên đọc field này, chỉ fallback về suy luận từ
   `data_coverage.channels_with_issues` cho report cũ sinh trước Sprint
   V3.3.4 (chưa có field `status`).
4. `POST /run`/`POST /retry` chạy **đồng bộ** (giữ 1 kết nối HTTP mở tới
   khi xong, không phải job async có job_id riêng) — widget bù lại bằng
   cách poll `GET /jobs` song song để có tiến trình theo thời gian thực,
   nhưng nếu người dùng đóng tab giữa chừng, lượt chạy vẫn tiếp tục ở
   server (không mất), chỉ cần mở lại và bấm "Làm mới" ở Report.
