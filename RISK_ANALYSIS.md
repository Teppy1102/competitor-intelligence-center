# RISK_ANALYSIS.md — Competitor Intelligence Center (Module 2)

> Sprint 1 — Deliverable 8/10. Đánh giá thẳng thắn theo Nguyên tắc 4 (CLAUDE.md): trình bày rõ đánh đổi và rủi ro, không né tránh.

## 1. Rủi ro pháp lý / Điều khoản dịch vụ (ToS) — **rủi ro cao nhất của toàn project**

**Mô tả:** Thu thập dữ liệu công khai từ Facebook/TikTok/LinkedIn qua bên thứ 3 (không qua API chính thức) thường vi phạm Điều khoản Dịch vụ của các nền tảng đó, dù dữ liệu là công khai và không cần đăng nhập.

**Mức độ:** Cao với LinkedIn, Trung bình với Facebook/TikTok, Thấp với YouTube (dùng API chính thức).

**Tác động nếu xảy ra:**
- Nhà cung cấp dữ liệu bên thứ 3 bị chặn/ngừng dịch vụ đột ngột → tính năng CIC cho nền tảng đó ngừng hoạt động không báo trước.
- Về mặt lý thuyết, nền tảng bị scrape có thể gửi yêu cầu ngừng hành vi (cease-and-desist) tới bên cung cấp dữ liệu — rủi ro này chủ yếu rơi vào nhà cung cấp thứ 3, nhưng LinkPower là bên sử dụng dịch vụ nên cần hiểu rõ đây không phải rủi ro bằng 0.

**Giảm thiểu:**
- Chỉ dùng dữ liệu **công khai** (không đăng nhập bằng tài khoản giả để lách quyền riêng tư).
- Ưu tiên provider có cam kết pháp lý rõ ràng, đã hoạt động lâu, có điều khoản dịch vụ minh bạch (Apify, Phantombuster thuộc nhóm này).
- Thiết kế hệ thống **chịu được** việc 1 nền tảng ngừng hoạt động bất kỳ lúc nào (Adapter fail gracefully — xem `ARCHITECTURE.md` §2.5), không để 1 provider chết kéo sập toàn hệ thống.
- Không launch LinkedIn cho đến khi có phương án rủi ro thấp hơn (xem `PLATFORM_STRATEGY.md`).

## 2. Rủi ro chất lượng & độ đầy đủ dữ liệu

**Mô tả:** Không giống MIC (search engine luôn trả về kết quả nếu chủ đề tồn tại), dữ liệu MXH có thể thiếu nghiêm trọng: tài khoản đối thủ ít hoạt động, provider bên thứ 3 chỉ trả được N bài gần nhất bất kể `time_range` yêu cầu, hoặc trang bị giới hạn quyền riêng tư một phần.

**Tác động:** Report chất lượng thấp, hoặc tệ hơn — AI bịa số liệu để "lấp đầy" nếu Rule Engine không đủ chặt.

**Giảm thiểu:** Đây là lý do toàn bộ `REPORT_SPECIFICATION_V1.md` được thiết kế xoay quanh khái niệm `completeness` và ngưỡng tối thiểu — không phải tính năng phụ, mà là **trụ cột thiết kế chính**. Ngưỡng cụ thể (vd: "≥ 5 bài") cần hiệu chỉnh lại sau khi có dữ liệu vận hành thật ở Sprint 2-3 (con số ở Sprint 1 là giả định hợp lý ban đầu, không phải số liệu đã kiểm chứng).

## 3. Rủi ro chi phí

| Nguồn chi phí | Ước tính giai đoạn | Ghi chú |
|---|---|---|
| OpenAI API (AI Analysis) | Tương đương/nhỉnh hơn MIC do prompt dài hơn (danh sách bài viết có cấu trúc) | Cần đo thực tế ở Sprint 2 trước khi ước tính chính xác |
| YouTube Data API | ~0 (trong free quota) | Rủi ro thấp |
| Third-party data provider (Facebook — nền tảng MVP chính) | **Ước tính $40-130/tháng** (gói nền tảng tối thiểu) + chi phí biên rất nhỏ theo lượt (~$0.25-0.80/report) — xem cách tính chi tiết ở `DATA_SOURCE_DESIGN.md` §6 | Đã duyệt ở mức nguyên tắc, **cần PoC Sprint 2 xác nhận số liệu chính xác** trước khi ký hợp đồng/cam kết dài hạn — con số hiện tại dựa trên mặt bằng giá phổ biến của thị trường, không phải báo giá chính thức |
| Third-party data provider (TikTok — Giai đoạn 2) | Chưa duyệt, ước tính tương tự Facebook | Nhắc lại quyết định ngân sách khi gần hoàn thành Facebook Adapter |
| Hosting (Render, tương tự MIC) | Tương đương MIC | Thấp |

**Khuyến nghị:** Con số $40-130/tháng cho Facebook là ngân sách **ở mức nguyên tắc** để LinkPower có cơ sở phê duyệt sơ bộ — không phải báo giá chính thức từ 1 provider cụ thể (Sprint 1 chưa chọn provider, xem `DATA_SOURCE_DESIGN.md` §2.2). Bắt buộc làm PoC đầu Sprint 2 trước khi ký hợp đồng dài hạn hoặc cam kết ngân sách chính xác.

## 4. Rủi ro kỹ thuật — thay đổi API/cấu trúc trang từ phía nền tảng

**Mô tả:** Facebook, TikTok, LinkedIn, kể cả YouTube, đều có thể thay đổi cấu trúc dữ liệu, giới hạn quota, hoặc chính sách truy cập bất kỳ lúc nào — nằm ngoài kiểm soát của LinkPower.

**Giảm thiểu:** Chính là lý do kiến trúc Adapter Pattern tồn tại (`ARCHITECTURE.md` §2.1) — cô lập rủi ro này vào đúng 1 file/nền tảng, không lan ra toàn hệ thống. Cần có `tests/fixtures/` (xem `FOLDER_STRUCTURE.md`) để phát hiện sớm khi 1 Adapter bắt đầu trả dữ liệu bất thường (test không phụ thuộc gọi API thật mỗi lần).

## 5. Rủi ro chất lượng phân tích AI (khác với rủi ro dữ liệu)

**Mô tả:** Ngay cả khi dữ liệu đầy đủ, các section định tính (Visual Analysis, Tone of Voice, SWOT) vẫn có nguy cơ AI "văn vẻ hoá" nếu prompt không đủ chặt — bài học trực tiếp từ MIC (từng phát hiện AI nhận diện sai đối thủ, xem lịch sử MIC).

**Giảm thiểu:** Áp dụng ngay từ đầu (không phải sửa sau như MIC):
- Quy tắc trích dẫn nguyên văn bắt buộc (§ REPORT_SPECIFICATION_V1.md mục 4, 5, 10).
- Section 9-11 (Audience, Positioning, SWOT) bắt buộc có `inference_basis`/kiểm tra chéo với section trước — không cho phép "bay tự do".
- Sprint 4 (Testing/Audit) phải có bước audit thủ công tương tự MIC đã làm (chạy N tài khoản mẫu, review kết quả có bịa không) trước khi coi MVP hoàn thành.

## 6. Rủi ro về kỳ vọng sai của người dùng nội bộ

**Mô tả:** Tên gọi "Competitor Intelligence" dễ khiến người dùng kỳ vọng có insight sâu như chủ sở hữu trang (reach, demographic, hiệu suất quảng cáo) — điều mà **không nền tảng nào** cho phép bên ngoài xem được (xem `DATA_SOURCE_DESIGN.md` §1).

**Giảm thiểu:** Ghi rõ trong UI/report (Executive Summary §1 của report luôn có `data_confidence_note`) rằng đây là phân tích dựa trên **dữ liệu công khai**, không phải insight nội bộ của đối thủ. Cần truyền đạt đúng kỳ vọng này cho stakeholder LinkPower ngay từ Sprint 1, không đợi đến khi launch mới giải thích.

## 7. Ma trận tổng hợp

| Rủi ro | Xác suất | Mức độ ảnh hưởng | Ưu tiên xử lý |
|---|---|---|---|
| ToS/pháp lý (Facebook/TikTok/LinkedIn) | Trung bình-Cao | Cao | Rất cao — quyết định chiến lược, không thể code fix |
| Dữ liệu thiếu/không đầy đủ | Cao | Trung bình (nếu Rule Engine tốt) → Cao (nếu Rule Engine yếu) | Rất cao — đã thiết kế giảm thiểu ngay từ Sprint 1 |
| Chi phí third-party vượt dự kiến | Trung bình | Trung bình | Cao — cần PoC trước khi cam kết |
| Thay đổi API đột ngột | Trung bình | Trung bình | Trung bình — đã cô lập qua Adapter Pattern |
| AI bịa/văn vẻ hoá | Trung bình | Cao (ảnh hưởng uy tín report) | Cao — áp dụng bài học từ MIC ngay từ đầu |
| Kỳ vọng sai của người dùng nội bộ | Trung bình | Thấp-Trung bình | Trung bình — xử lý bằng truyền thông + UI, không phải code |
