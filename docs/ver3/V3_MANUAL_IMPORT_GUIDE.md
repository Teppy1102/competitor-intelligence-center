# V3_MANUAL_IMPORT_GUIDE.md — Sprint V3.2

> Hướng dẫn nhập dữ liệu thủ công cho kênh LinkedIn/TikTok (hoặc Facebook
> khi Apify không khả dụng) — xem
> [`V3_COLLECTION_PROVIDER_GUIDE.md`](./V3_COLLECTION_PROVIDER_GUIDE.md) để
> hiểu khi nào hệ thống yêu cầu bước này.

## 1. Khi nào cần Manual Import

Sau khi bấm "Chạy Benchmark", nếu 1 kênh có trạng thái **"Cần nhập thủ
công"** (`requires_manual_input`), nghĩa là hệ thống chưa có cách tự động
thu thập dữ liệu cho kênh đó (LinkedIn/TikTok mặc định, hoặc Facebook khi
chưa cấu hình Apify). Bạn cần chuẩn bị file dữ liệu và upload qua nút
**"Nhập dữ liệu"** ngay tại dòng kênh đó.

## 2. File mẫu

```
docs/ver3/samples/linkedin_import_template.csv
docs/ver3/samples/tiktok_import_template.csv
```

Có thể dùng CSV hoặc JSON — 2 định dạng chấp nhận field giống nhau.

## 3. Cấu trúc file

### CSV

Dòng đầu tiên là header, dùng đúng tên cột dưới đây (không bắt buộc đủ hết
— chỉ `external_content_id` và (`text_content` hoặc `title`) là bắt buộc).
Các field dạng danh sách (`media_urls`, `hashtags`, `mentions`,
`external_links`) dùng dấu `|` để phân tách nhiều giá trị trong 1 ô — **không
dùng dấu phẩy** (dễ nhầm với dấu phân tách cột CSV).

| Cột | Bắt buộc | Kiểu | Ghi chú |
|---|---|---|---|
| `external_content_id` | ✔ | text | ID bài viết gốc (tự đặt, cần duy nhất trong 1 kênh) |
| `text_content` hoặc `title` | ✔ (1 trong 2) | text | Nội dung/caption |
| `published_at` | khuyến nghị | ISO 8601 (`2026-06-01T09:00:00Z`) | Thiếu sẽ khiến metric Activity kém chính xác |
| `content_type` | khuyến nghị | `text`/`image`/`video`/`carousel`/... | |
| `author_name`, `author_url` | | text | |
| `description` | | text | |
| `media_urls`, `hashtags`, `mentions`, `external_links` | | text (phân tách bằng `\|`) | |
| `thumbnail_url` | | URL | |
| `video_duration` | | số nguyên (giây) | Chỉ dùng cho video/TikTok |
| `cta_text` | | text | |
| `language` | | `vi`/`en`/... | |
| `view_count`, `like_count`, `reaction_count`, `comment_count`, `share_count`, `save_count` | | số nguyên | Để trống nếu không biết — **không điền 0** nếu không chắc |
| `follower_count_at_collection` | | số nguyên | Số follower tại thời điểm bạn lấy dữ liệu |

### JSON

```json
{
  "items": [
    {
      "external_content_id": "li-post-001",
      "published_at": "2026-06-01T09:00:00Z",
      "content_type": "text",
      "text_content": "Khai giảng khóa HRBP tháng 6 - đăng ký ngay!",
      "hashtags": ["#HRBP", "#LinkPower"],
      "like_count": 45,
      "comment_count": 6,
      "share_count": 3,
      "follower_count_at_collection": 5200
    }
  ]
}
```

Hoặc gửi thẳng 1 mảng `[ {...}, {...} ]` (không cần bọc `"items"`).

## 4. Quy tắc "null khác 0"

**Chỉ điền số khi bạn chắc chắn giá trị thật.** Để trống (CSV) hoặc `null`/bỏ
qua field (JSON) nếu không rõ — hệ thống hiểu:

```
Trống/null = "không có dữ liệu" (không tính vào công thức trung bình/tổng)
0          = "biết chắc là 0" (vẫn tính vào công thức)
```

Điền nhầm 0 khi thực ra không biết sẽ làm méo kết quả Benchmark (kéo
`engagement_rate`, `posts_per_week`... xuống sai lệch).

## 5. Giới hạn

| Giới hạn | Giá trị |
|---|---|
| Kích thước file tối đa | 2 MB |
| Số dòng tối đa/lần import | 200 dòng |
| Định dạng chấp nhận | `.csv`, `.json` (theo đúng đuôi file) |

## 6. An toàn dữ liệu khi import

- Hệ thống tự động **vô hiệu hoá công thức Excel/Sheets** (chống CSV
  Formula Injection): nếu 1 ô bắt đầu bằng `=`, `+`, `-`, `@`, hệ thống tự
  thêm dấu `'` phía trước để trình soạn thảo bảng tính không thực thi nội
  dung đó như công thức.
- File không được thực thi — chỉ được đọc bằng parser CSV/JSON chuẩn
  (không `eval`, không chạy script từ file).
- Dữ liệu hiển thị trên giao diện luôn được escape HTML trước khi render
  (chống XSS) — kể cả dữ liệu bạn tự nhập.

## 7. Sau khi import

1. Hệ thống báo số dòng hợp lệ / tổng số dòng đã đọc, kèm danh sách lỗi
   theo từng dòng (nếu có).
2. Dữ liệu được lưu ngay (gắn `provider = "manual_import"`), **nhưng chưa
   tự động chạy lại phân tích**.
3. Bấm lại **"Chạy Benchmark"** để hệ thống dùng dữ liệu vừa nhập, tính
   lại metric/benchmark/report cho toàn bộ dự án.
4. Có thể import nhiều lần cho cùng 1 kênh — dữ liệu **không bị nhân đôi**
   (idempotent theo `external_content_id`), lần import sau ghi đè đúng
   bài trùng ID.

## 8. Xem trước trước khi lưu

Endpoint `POST /api/v3/benchmark/import/preview` (chưa có nút riêng trên
UI ở Sprint V3.2, dành cho tích hợp API/Sprint sau) cho phép xem 10 dòng
đầu tiên + danh sách lỗi **mà không ghi vào cơ sở dữ liệu** — dùng để kiểm
tra file trước khi import thật qua `POST /api/v3/benchmark/import`.
