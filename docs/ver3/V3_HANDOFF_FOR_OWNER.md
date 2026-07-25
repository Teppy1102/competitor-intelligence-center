# V3 Handoff for Owner

**Trạng thái: Ver 3 đã deploy production và UAT thật đã chạy xong (xem `V3_UAT_REPORT.md`).**

## 1. Backend production

`https://competitor-intelligence-center-api.onrender.com`

Database: PostgreSQL (`cic-v3-postgres`) — đã xác nhận `connected: true`,
`schema_ready: true` qua `GET /api/v3/health/db`.

## 2. File HTML cần copy vào LadiPage

`dist/ladipage/ver3-social-benchmark-embed.html`

## 3. Các bước dán vào LadiPage (≤10 bước)

1. Mở `dist/ladipage/ver3-social-benchmark-embed.html` bằng trình soạn thảo (VS Code, Notepad...).
2. Chọn toàn bộ nội dung (Ctrl+A), copy (Ctrl+C).
3. Vào LadiPage → trang cần nhúng → thêm 1 khối "HTML/Code" (Custom Code).
4. Dán toàn bộ nội dung vào khối đó (Ctrl+V).
5. Không sửa gì khác — ô "Backend API" đầu widget đã điền sẵn đúng URL production.
6. Lưu (Save) trang LadiPage.
7. Bấm Preview — kiểm tra chấm tròn "Kết nối OK" ở khối cấu hình đầu trang.
8. Publish trang.
9. Mở trang đã publish trên trình duyệt thật (không phải chế độ preview).
10. Test nhanh theo mục 4 bên dưới.

## 4. Test nhanh sau khi publish (≤5 bước)

1. Tạo 1 project test, thêm brand LinkPower (kênh Facebook) + 1 đối thủ (kênh LinkedIn/TikTok).
2. Bấm "Chạy Benchmark" — chờ xong, xác nhận report A–J hiển thị (Facebook tự động qua Apify; LinkedIn/TikTok báo "Cần nhập thủ công").
3. Thử Manual Import 1 file CSV/JSON mẫu (`docs/ver3/samples/`) cho kênh LinkedIn/TikTok, bấm "Thử lại kênh này".
4. Kiểm tra badge trạng thái report chuyển đúng (một phần → hoàn tất đầy đủ).
5. Đóng tab, mở lại trang (F5) — xác nhận project và report cũ vẫn còn (Report History).

## 5. Provider đang dùng trên production

| Nền tảng | Provider | Ghi chú |
|---|---|---|
| Facebook | `apify` (tự động) | Đã UAT thật, thu thập dữ liệu thành công |
| LinkedIn | `manual_import` | Upload CSV/JSON theo mẫu `docs/ver3/samples/linkedin_import_template.csv` |
| TikTok | `manual_import` | Upload CSV/JSON theo mẫu `docs/ver3/samples/tiktok_import_template.csv`. Actor Apify thật (`external`) hiện bị Apify Free Plan chặn (trả demo data) — cần nâng gói Apify trả phí mới dùng được, **chưa tự nâng gói** |

## 6. Cách rollback về Ver 2

Trên Render Dashboard → service `competitor-intelligence-center-api` →
Environment → đặt `ENABLE_SOCIAL_BENCHMARK=false` → Save (service tự
redeploy). Toàn bộ route `/api/v3/*` biến mất ngay, `POST
/api/competitor/facebook` (Ver 1/2) không đổi. Muốn rollback code hoàn
toàn: nút **Rollback** trên Render Dashboard, chọn lần deploy trước commit
`1c5697b` (merge Ver 3 đầu tiên).

## 7. Bật LinkedIn/TikTok live provider sau này

Đổi `LINKEDIN_PROVIDER` / `TIKTOK_PROVIDER` từ `manual_import` sang
`external` trên Render Environment (không cần sửa code) — TikTok cần nâng
gói Apify trả phí trước (xem mục 5).

## 8. Sự cố ngoài phạm vi kỹ thuật cần bạn xử lý

Domain `linkpower.vn` (gồm `edu.linkpower.vn`) hiện **không resolve DNS
được** (xác nhận qua Google Public DNS — nameserver Route53 được uỷ quyền
từ chối mọi truy vấn). Đây là sự cố DNS/registrar, không liên quan Render
hay code — cần bạn kiểm tra lại cấu hình DNS/hosted zone. Trang LadiPage sẽ
không truy cập được cho tới khi domain này được khôi phục.
