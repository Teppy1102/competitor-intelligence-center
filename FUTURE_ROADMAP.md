# FUTURE_ROADMAP.md — Competitor Intelligence Center (Module 2)

> Sprint 1 — Deliverable 10/10. Định hướng sau MVP — không cam kết timeline cụ thể ở Sprint 1, chỉ xác nhận kiến trúc hiện tại không chặn các hướng mở rộng này.

## 1. Mở rộng nền tảng (theo `PLATFORM_STRATEGY.md`)

- **Giai đoạn 2:** Facebook Adapter + TikTok Adapter (qua third-party data provider đã duyệt).
- **Giai đoạn 3:** Đánh giá lại LinkedIn khi có phương án dữ liệu rủi ro thấp hơn.
- **Giai đoạn 4:** Website Intelligence — mở rộng khỏi phạm vi "mạng xã hội", Adapter mới sẽ crawl website đối thủ (trang chủ, trang khoá học, blog) thay vì gọi API MXH. Report Specification cho Website Intelligence sẽ cần thiết kế riêng (không dùng nguyên 13 section hiện tại — vd: thay Publishing Pattern bằng SEO/Content Freshness, thay Visual Analysis bằng UX/Page Speed) nhưng vẫn dùng chung Analysis Engine + Rule Engine + Job Store nếu tuân thủ đúng `NormalizedProfile`/`NormalizedPost`-tương-đương cho website.

## 2. Competitor Monitoring định kỳ (Recurring Analysis)

**Ý tưởng:** Thay vì user chủ động chạy 1 lần, hệ thống tự động chạy lại phân tích cho các đối thủ đã lưu theo lịch (vd: hàng tuần/hàng tháng), và **so sánh report mới với report cũ** để phát hiện thay đổi đáng chú ý.

**Yêu cầu kiến trúc bổ sung (chưa có ở MVP):**
- Cần lưu trữ có cấu trúc hơn file JSON đơn lẻ hiện tại — cân nhắc chuyển sang DB nhẹ (SQLite hoặc Postgres) khi số lượng job tăng, vì file-based job store (đúng như MIC) phù hợp cho phân tích một-lần nhưng không tối ưu cho truy vấn lịch sử/so sánh theo thời gian.
- Cần cơ chế lập lịch (cron/scheduled job) — hiện tại `main.py` chỉ có BackgroundTasks phản ứng theo request, chưa có tác vụ định kỳ.
- Cần thiết kế "Diff Report" — so sánh 2 `CompetitorDataset` theo thời gian, phát hiện: đối thủ tăng/giảm tần suất đăng bài, đổi content pillar chính, xuất hiện chiến dịch mới.

## 3. Market Alert

**Ý tưởng:** Cảnh báo chủ động khi phát hiện thay đổi đáng chú ý ở đối thủ đang theo dõi (dựa trên Competitor Monitoring ở §2), gửi qua email/Zalo/Slack nội bộ LinkPower.

**Phụ thuộc:** Cần §2 hoàn thành trước. Ngưỡng "đáng chú ý" cần thiết kế cẩn thận để tránh spam thông báo (vd: chỉ cảnh báo khi tần suất đăng bài tăng > 50% hoặc xuất hiện content pillar hoàn toàn mới).

## 4. Content Gap Analysis độc lập (không cần chọn 1 đối thủ cụ thể)

**Ý tưởng:** Mở rộng từ section 12 (Benchmark) hiện tại — thay vì so 1-1 với 1 đối thủ, tổng hợp Content Gap từ **nhiều đối thủ đã phân tích trước đó** để có bức tranh thị trường rộng hơn (gần với vai trò của MIC nhưng nhìn từ góc độ nội dung MXH thay vì tìm kiếm).

**Phụ thuộc:** Cần đã có đủ dữ liệu lịch sử từ nhiều lần phân tích (§2), và cần thiết kế cách tổng hợp nhiều `CompetitorDataset` cùng lúc — chưa có trong scope Sprint 1.

## 5. AI Recommendation nâng cao (chủ động, không chỉ theo yêu cầu)

**Ý tưởng:** Thay vì chỉ trả lời khi user chủ động yêu cầu phân tích, hệ thống tự đề xuất "LinkPower nên chú ý đối thủ nào tiếp theo" dựa trên tín hiệu thị trường (tăng trưởng follower bất thường, xuất hiện trên nhiều kết quả tìm kiếm — có thể liên kết ngược với Module 1/MIC ở đây).

## 6. Tích hợp vào Marketing Intelligence Platform (tầm nhìn dài hạn theo đề bài gốc)

Đề bài gốc xác định đích đến cuối cùng là 1 nền tảng chung, không phải các module rời rạc. Ghi nhận các điểm cần đồng bộ khi tới giai đoạn tích hợp thật (chưa thiết kế chi tiết ở Sprint 1, chỉ liệt kê để không thiết kế CIC theo hướng đóng kín):

- **Xác thực người dùng dùng chung** giữa MIC và CIC (hiện cả 2 đều chưa có auth — cần thiết kế khi có nhiều module).
- **Job Store dùng chung hoặc liên thông** — hiện MIC và CIC đều lưu file riêng biệt trong `reports/` của từng project; khi tích hợp cần cân nhắc 1 data layer chung hoặc ít nhất 1 chuẩn đặt tên/`job_id` không xung đột giữa các module.
- **Điều hướng chung (Platform Shell)** — 1 giao diện chủ cho user chọn vào MIC hay CIC hay module tương lai, thay vì 2 domain/route độc lập như hiện tại (`edu.linkpower.vn/research` cho MIC).
- **Chuẩn hoá "Report" như 1 khái niệm chung** — cả MIC và CIC đều đang dùng chung triết lý (HTML `<h2>` đánh số → JSON → Dashboard). Đây là tài sản kiến trúc quan trọng nhất có thể nâng cấp thành 1 "Report Engine" dùng chung cho mọi module tương lai của LinkPower AI, thay vì mỗi module tự viết `report_parser.py`/`render.py` riêng như hiện tại (MIC và CIC ở Sprint 1-5 vẫn cố ý tách riêng để giảm rủi ro phụ thuộc chéo giữa 2 project đang phát triển song song — hợp nhất là bước tối ưu **sau khi** cả 2 đã ổn định).

## 7. Nguyên tắc chung khi lên roadmap các mục trên

Không mục nào ở trên được phép **phá vỡ** 2 hợp đồng cốt lõi đã thiết lập ở Sprint 1:
1. `PlatformAdapter` interface (`ARCHITECTURE.md` §4).
2. `NormalizedProfile`/`NormalizedPost`/`CompetitorDataset` schema (`ARCHITECTURE.md` §5, có versioning ở §6).

Nếu 1 hạng mục roadmap tương lai đòi hỏi phá vỡ 1 trong 2 hợp đồng này, đó là dấu hiệu cần quay lại xem xét kiến trúc gốc, không phải chỉ "thêm field" tuỳ tiện.
