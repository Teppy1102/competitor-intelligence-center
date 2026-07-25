# V3 Handoff for Owner

**Backend production URL:** `https://competitor-intelligence-center-api.onrender.com`
(đã chạy Facebook MVP — **Ver 3 chưa deploy tại thời điểm viết tài liệu này**,
xem `V3_SPRINT_034_FINAL_REPORT.md` mục Blocker).

## Environment variables cần thêm/xác nhận trên Render Dashboard

| Biến | Việc cần làm |
|---|---|
| `OPENAI_API_KEY` | Xác nhận còn hợp lệ (lấy tại platform.openai.com/api-keys) |
| `APIFY_API_TOKEN` | Xác nhận còn hợp lệ (lấy tại console.apify.com/settings/integrations) |

Tất cả biến khác (`ALLOWED_ORIGINS`, `DATABASE_URL`, `LINKEDIN_PROVIDER`...)
đã cố định sẵn trong `render.yaml`, tự áp dụng khi deploy — không cần nhập
tay. Chi tiết đầy đủ: `V3_PRODUCTION_ENV_GUIDE.md`.

## File HTML cần copy vào LadiPage

`dist/ladipage/ver3-social-benchmark-embed.html` (bản đầy đủ) — khuyến nghị
dùng `dist/ladipage/ver3-social-benchmark-embed.min.html` (bản nén) khi dán
thật vào LadiPage.

## Các bước dán vào LadiPage (tối đa 10 bước)

1. Deploy backend trước (xem `V3_DEPLOYMENT_GUIDE.md`) — file HTML sẽ không
   chạy được nếu backend chưa phục vụ `/api/v3/*`.
2. Mở `dist/ladipage/ver3-social-benchmark-embed.min.html` bằng trình soạn thảo, copy toàn bộ nội dung.
3. Vào LadiPage → trang cần nhúng → thêm 1 khối "HTML/Code" (Custom Code).
4. Dán toàn bộ nội dung vào khối đó.
5. Không sửa gì khác trong khối này trừ khi cần đổi Backend URL (xem bước 6).
6. Nếu Backend URL khác mặc định: tìm ô "Backend API URL" ngay trong khối cấu hình đầu trang preview, nhập URL đúng — hệ thống tự lưu lại (localStorage), không cần sửa code.
7. Lưu (Save) trang LadiPage.
8. Bấm Preview — kiểm tra đèn trạng thái kết nối (chấm xanh = OK) ở khối cấu hình.
9. Publish trang.
10. Mở trang đã publish trên trình duyệt thật (không phải preview mode) để xác nhận chạy đúng.

## Test nhanh sau khi publish (tối đa 5 bước)

1. Tạo 1 project test, thêm 1 kênh LinkPower + 1 đối thủ (LinkedIn/TikTok).
2. Bấm "Chạy Benchmark" — chờ xong, xác nhận có report A–J hiển thị.
3. Kiểm tra badge trạng thái report (Hoàn tất đầy đủ / một phần / cần nhập thủ công) khớp với dữ liệu thật.
4. Thử Manual Import 1 file CSV/JSON mẫu cho 1 kênh.
5. Mở lại trang (F5) — xác nhận project/report cũ vẫn còn (Report History).

## Cách rollback về Ver 2

Trên Render Dashboard, đặt biến môi trường `ENABLE_SOCIAL_BENCHMARK=false`
(không cần deploy lại, service tự áp dụng khi restart) — toàn bộ route
`/api/v3/*` biến mất ngay, `POST /api/competitor/facebook` (Ver 1/2) không
đổi. Muốn rollback code hoàn toàn: dùng nút **Rollback** trên Render
Dashboard, chọn lần deploy trước Sprint V3.3.4.
