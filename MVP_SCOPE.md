# MVP_SCOPE.md — Competitor Intelligence Center (Module 2)

> Sprint 1 — Deliverable 9/10. Định nghĩa rõ ràng "Done" cho MVP để Sprint 2-5 có mục tiêu cụ thể, tránh scope creep.
>
> **Cập nhật sau khi LinkPower duyệt (xem `README.md` mục Quyết định đã duyệt):** LinkPower xác nhận **ưu tiên Facebook** nếu phải chọn 1 nền tảng để launch trước — đảo ngược đề xuất ban đầu của Sprint 1 (vốn đề xuất YouTube trước vì rủi ro/chi phí thấp hơn). Mục 4 dưới đây giữ nguyên lý do kỹ thuật của đề xuất gốc để làm tài liệu tham khảo, nhưng **MVP chính thức đi theo quyết định của LinkPower: Facebook là nền tảng chính**.

## 1. Trong phạm vi MVP (In Scope)

| Hạng mục | Quyết định MVP |
|---|---|
| Nền tảng chính (bắt buộc có ở MVP) | **Facebook** (theo quyết định của LinkPower) — qua third-party data provider, xem `DATA_SOURCE_DESIGN.md` |
| Nền tảng bổ sung (khuyến nghị làm cùng vì chi phí ~0) | **YouTube** — do dùng API chính thức miễn phí, chi phí công sức thêm vào rất thấp so với giá trị kiểm chứng kiến trúc Adapter Pattern bằng 2 nguồn dữ liệu khác hẳn nhau (official API vs third-party). Nếu Sprint 2 thiếu thời gian, có thể lùi YouTube sang ngay đầu Sprint 3 mà không ảnh hưởng MVP chính |
| Nền tảng nhận diện được nhưng chưa xử lý | LinkedIn, TikTok — trả thông báo rõ ràng "chưa hỗ trợ", không lỗi hệ thống |
| Time range | 1 / 3 / 6 tháng — đủ cả 3 |
| Số section report | Đủ 13 section theo `REPORT_SPECIFICATION_V1.md` |
| Visual Analysis (section 6) | Mặc định **"Không đủ dữ liệu"** ở MVP — chưa tích hợp Vision model phân tích ảnh/thumbnail (xem §3 Out of Scope) |
| Benchmark (section 12) | Có — thu thập dữ liệu Fanpage Facebook (và kênh YouTube nếu làm cùng) của LinkPower song song, dùng URL thật đã cung cấp (xem §5) |
| KPI Scores | Đủ 7 score theo `REPORT_SPECIFICATION_V1.md` §14 |
| Dashboard/UI | Tái sử dụng phong cách MIC, không thiết kế mới — theo đúng yêu cầu đề bài |
| Download HTML | Có, giống MIC |
| History (danh sách các lần phân tích trước) | Có, giống MIC (đã có `/api/history` pattern) |
| Job xử lý bất đồng bộ + polling | Có, tái dùng nguyên pattern MIC |
| Anti-fabrication Rule Engine | Có — bắt buộc, không phải "nice to have" |

## 2. Tiêu chí "Done" của MVP (Definition of Done)

MVP được coi là hoàn thành khi **tất cả** điều kiện sau đạt:

1. User dán 1 URL Facebook Page hợp lệ + chọn time range → nhận được report đầy đủ 13 section trong thời gian chấp nhận được (đề xuất ngưỡng ban đầu: dưới 5 phút — Facebook qua third-party thường chậm hơn official API, điều chỉnh sau khi đo thật ở PoC Sprint 2).
2. User dán URL LinkedIn/TikTok → nhận thông báo rõ ràng "chưa hỗ trợ", không phải lỗi 500.
3. Chạy thử với ≥ 5 Fanpage mẫu đa dạng (Fanpage hoạt động mạnh, ít hoạt động, mới lập ít bài) → không có trường hợp nào AI bịa số liệu không có trong dữ liệu thật (audit thủ công, tương tự quy trình đã áp dụng cho MIC).
4. Benchmark hoạt động đúng: dùng Fanpage `facebook.com/LinkPowerVN` (xem §5) để so sánh thật; nếu provider không lấy được dữ liệu LinkPower ở 1 lần chạy cụ thể, section 12 trả "Không đủ dữ liệu" thay vì lỗi.
5. Toàn bộ pipeline có test tự động cho `engine/report_parser.py` và `engine/rules.py` (không phụ thuộc gọi API thật) — kế thừa đúng "Coding Standard: Testing" trong đề bài gốc.
6. PoC Sprint 2 đã xác nhận chi phí thực tế của data provider Facebook nằm trong khoảng ước tính ở §5 (hoặc báo cáo lệch để LinkPower duyệt lại ngân sách trước khi tích hợp chính thức).
7. Deploy thành công lên Render (hoặc hạ tầng tương đương MIC), có domain/route riêng, sẵn sàng để LinkPower duyệt trước khi công bố nội bộ.
8. *(Nếu làm cùng YouTube ở MVP)* Adapter YouTube hoạt động đúng như mô tả ở bản Sprint 1 gốc — dùng để kiểm chứng chéo kiến trúc Adapter Pattern hoạt động tốt với cả nguồn official API lẫn third-party.

## 3. Ngoài phạm vi MVP (Out of Scope — cố ý, không phải thiếu sót)

| Hạng mục | Lý do loại khỏi MVP | Khi nào xem xét lại |
|---|---|---|
| TikTok Adapter thật | Cần duyệt ngân sách riêng + chọn provider (xem `DATA_SOURCE_DESIGN.md`) | Giai đoạn 2 — `PLATFORM_STRATEGY.md` |
| LinkedIn Adapter thật | Rủi ro pháp lý cao nhất, chưa có phương án an toàn | Giai đoạn 3, chưa cam kết thời điểm |
| Visual Analysis bằng Vision model (phân tích ảnh/thumbnail thật) | Tăng chi phí + độ phức tạp đáng kể, chưa cần thiết để chứng minh giá trị cốt lõi (phân tích content/tone/publishing pattern) | Sau khi MVP Facebook được LinkPower duyệt, đánh giá ROI trước khi thêm |
| Competitor Monitoring định kỳ tự động (chạy lại theo lịch, cảnh báo thay đổi) | Đây là tính năng của "Market Alert" trong Roadmap, không phải MVP một-lần-phân-tích | `FUTURE_ROADMAP.md` |
| Đa ngôn ngữ report (hiện chỉ tiếng Việt) | Ngoài phạm vi đề bài gốc | Không xác định |
| Phân tích nhiều đối thủ cùng lúc / so sánh nhiều đối thủ | Đề bài gốc chỉ yêu cầu "nghiên cứu CHÍNH MỘT đối thủ" | `FUTURE_ROADMAP.md` nếu có nhu cầu |

## 4. Lý do đề xuất ban đầu (Sprint 1) là YouTube trước — giữ lại làm tài liệu tham khảo

*(Phần này giữ nguyên để ghi lại lý do kỹ thuật của đề xuất gốc — LinkPower đã cân nhắc và quyết định ưu tiên Facebook, đề xuất dưới đây không còn là quyết định chính thức nhưng vẫn hữu ích để hiểu rõ đánh đổi.)*

1. **Rủi ro kỹ thuật/pháp lý gần như bằng 0** — cho phép đội dev tập trung 100% năng lượng vào việc làm đúng phần khó nhất và giá trị nhất: AI Analysis Engine + Rule Engine + Report Specification, thay vì vừa làm vừa vá lỗi nguồn dữ liệu không ổn định.
2. **Validate kiến trúc Adapter Pattern bằng dữ liệu thật**, không phải bằng lý thuyết.
3. **Chi phí gần như bằng 0** so với Facebook cần ngân sách data provider ngay từ đầu.

**Vì sao vẫn ưu tiên Facebook theo quyết định của LinkPower là hợp lý:** Facebook là kênh truyền thông chính cho tuyển sinh/sự kiện của ngành đào tạo doanh nghiệp tại Việt Nam — giá trị kinh doanh của báo cáo Facebook cao hơn đáng kể so với YouTube trong ngắn hạn, bù lại cho chi phí/rủi ro tăng thêm. Đây là đánh đổi hợp lý miễn LinkPower đã hiểu rõ rủi ro ở `RISK_ANALYSIS.md` §1 và ngân sách ước tính ở §5 dưới đây.

## 5. Thông tin đã được LinkPower cung cấp/duyệt (chốt tại thời điểm này)

| Mục | Giá trị |
|---|---|
| Ưu tiên nền tảng MVP | **Facebook** (nếu chỉ chọn 1) |
| Fanpage Facebook chính thức của LinkPower | `https://www.facebook.com/LinkPowerVN` |
| Kênh YouTube chính thức của LinkPower | `https://www.youtube.com/@LinkPower` |
| TikTok chính thức của LinkPower | `https://www.tiktok.com/@linkpower.vn` |
| LinkedIn Company chính thức của LinkPower | `https://vn.linkedin.com/company/linkpowervn` |
| Ngân sách data provider Facebook | Đã duyệt ở mức nguyên tắc, con số ước tính cụ thể xem `DATA_SOURCE_DESIGN.md` §6 — **cần PoC Sprint 2 xác nhận trước khi cam kết chính thức** |

Cả 4 URL trên sẽ được đưa vào `config.json` → `linkpower_profiles.*` (xem `FOLDER_STRUCTURE.md` §3) ngay từ Sprint 2. Lưu ý: có đủ URL LinkPower cho cả 4 nền tảng **không làm thay đổi** thứ tự triển khai Adapter ở `PLATFORM_STRATEGY.md` (Facebook → YouTube → TikTok → LinkedIn) — đây vẫn là quyết định dựa trên độ khả thi kỹ thuật/rủi ro của từng nền tảng (`DATA_SOURCE_DESIGN.md`), không phải do thiếu dữ liệu Benchmark. Khi Adapter LinkedIn/TikTok chưa tồn tại, Benchmark trên 2 nền tảng đó vẫn trả "Không đủ dữ liệu" dù đã có URL cấu hình sẵn — vì bản thân dữ liệu đối thủ trên nền tảng đó cũng chưa thu thập được.
