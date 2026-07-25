# V3_PRODUCT_REQUIREMENTS.md — Social Competitor Benchmark (Sprint V3.1)

> Dựa trên đề bài Sprint V3.1 + `V3_CURRENT_SYSTEM_AUDIT.md`. Ver 3 mở rộng
> Module 2 (`COMPETITOR_INTELLIGENCE_CENTER`) — không phải sản phẩm mới.

## 1. Mục tiêu Ver 3

1. Cho phép phân tích đối thủ trên **LinkedIn** và **TikTok**, ngoài Facebook
   đã có.
2. Cho phép benchmark **nhiều đối thủ cùng lúc** trên cùng hệ thống (không
   còn giới hạn 1-đối-thủ-1-lần như CIC hiện tại).
3. Cho phép **so sánh LinkPower với từng đối thủ và với cả nhóm đối thủ**.
4. Xuất được **report benchmark có cấu trúc rõ ràng** (không chỉ đoạn văn AI).
5. Chuẩn bị **nền móng dữ liệu** để Ver 4 (Marketing Direction) dùng lại kết
   quả Ver 1+2+3 mà không phải phân tích lại từ đầu.

## 2. Ngoài phạm vi (Out of scope — Sprint V3.1)

- Xây hoàn chỉnh scraper/provider LinkedIn hoặc TikTok thật (chỉ cần
  contract + Mock/Manual Import provider — xem `V3_ARCHITECTURE.md` §5).
- Tự động tìm đối thủ (người dùng luôn chủ động nhập URL).
- Ver 4 (Marketing Direction) — chỉ chuẩn bị data model để tái sử dụng.
- Thay đổi/phá vỡ bất kỳ route, contract, hay hành vi nào của Ver 1/Ver 2
  đang chạy production.
- Thêm database mới, đổi framework, đổi cơ chế deploy.
- Benchmark có trọng số tối ưu bằng ML — công thức phải minh bạch, có thể
  giải thích (xem `V3_BENCHMARK_SPEC.md`).

## 3. User Personas

| Persona | Vai trò | Nhu cầu chính với Ver 3 |
|---|---|---|
| **Marketing Manager LinkPower** | Người dùng chính, thao tác trực tiếp trên `/research` | Nhập nhanh 3-5 đối thủ trên nhiều nền tảng, xem ngay LinkPower đang mạnh/yếu ở đâu |
| **Ban Giám đốc** | Người đọc report, không thao tác hệ thống | Cần dashboard tóm tắt dễ hiểu, số liệu có nguồn gốc rõ (không tin AI bịa) |
| **Đội Content/Social** | Dùng insight để lên kế hoạch nội dung | Cần chi tiết content pillar, hook/CTA, thời điểm đăng của đối thủ |
| **Kỹ sư vận hành (Sprint sau)** | Người triển khai LinkedIn/TikTok Adapter thật ở V3.2+ | Cần contract rõ ràng, không phải đoán ý đồ kiến trúc |

## 4. User Stories

1. *Là Marketing Manager*, tôi chọn 1 hoặc nhiều nền tảng (Facebook/LinkedIn/
   TikTok), nhập 1 kênh LinkPower + nhiều đối thủ, để nhận 1 report benchmark
   duy nhất so sánh tất cả.
2. *Là Marketing Manager*, khi tôi dán 1 URL sai định dạng hoặc trùng với
   URL đã nhập, tôi muốn thấy lỗi rõ ràng ngay tại chỗ, không phải đợi hết
   job mới biết.
3. *Là Marketing Manager*, khi 1 trong N đối thủ thu thập dữ liệu thất bại,
   tôi vẫn muốn nhận được report cho N-1 đối thủ còn lại, kèm cảnh báo rõ
   ràng đối thủ nào bị thiếu và vì sao.
4. *Là Ban Giám đốc*, tôi muốn mỗi điểm số benchmark có công thức/nguồn dữ
   liệu tra cứu được, không phải điểm AI "cảm tính".
5. *Là đội Content*, tôi muốn xem đối thủ nào đang dùng content pillar nào
   nhiều nhất, để tránh trùng lặp hoặc học hỏi định dạng hiệu quả.
6. *Là kỹ sư Sprint V3.2*, tôi muốn thêm LinkedIn Adapter thật bằng cách chỉ
   viết 1 file mới implement `PlatformAdapter`, không phải sửa
   `engine/pipeline.py` hay `benchmark/`.
7. *Là hệ thống Ver 4 (tương lai)*, tôi muốn đọc lại `normalized_social_items`
   + `benchmark_results` đã lưu của Ver 3 mà không cần gọi lại Adapter/AI.

## 5. Functional Requirements

| # | Yêu cầu | Nguồn |
|---|---|---|
| FR1 | Hệ thống nhận diện nền tảng (Facebook/LinkedIn/TikTok) từ URL qua `detect_platform()` mở rộng | Đề bài Mục 9 |
| FR2 | Chuẩn hoá URL: bỏ tracking params, xử lý `/` cuối, nhận diện URL không hợp lệ | Đề bài Mục 9 |
| FR3 | Chặn URL trùng trong cùng 1 project/benchmark run | Đề bài Bước 4 |
| FR4 | Hỗ trợ nhập 1 kênh LinkPower + N đối thủ, 1 brand có thể có nhiều nền tảng | Đề bài Bước 2 |
| FR5 | Mỗi URL/channel có trạng thái thu thập độc lập (Pending/Collecting/Collected/Partially collected/Failed/Requires manual input) | Đề bài Bước 5 |
| FR6 | 1 URL lỗi không làm crash toàn bộ job — job tiếp tục với N-1 kênh còn lại | Đề bài Bước 4, kế thừa nguyên tắc "fail gracefully" đã có ở CIC |
| FR7 | Dữ liệu Facebook/LinkedIn/TikTok được chuẩn hoá về schema chung trước khi phân tích | Đề bài Bước 6, tái dùng `NormalizedProfile`/`NormalizedPost` |
| FR8 | Adapter mới (LinkedIn/TikTok/ManualImport/Mock) implement đúng `PlatformAdapter` hiện có, không sửa interface | Nguyên tắc 3.4 |
| FR9 | Hệ thống hỗ trợ nhiều data provider/nền tảng qua provider abstraction (Official API/third-party/manual/mock) | Nguyên tắc 3.3 |
| FR10 | Benchmark so sánh LinkPower với từng đối thủ VÀ với toàn nhóm đối thủ đã nhập | Đề bài Bước 8, Mục 4 |
| FR11 | Mọi benchmark score có công thức rõ ràng, không dựa cảm tính AI | Mục 6 |
| FR12 | Report/Dashboard đồng bộ giao diện với `/research` hiện tại, không tạo site mới | Nguyên tắc 3.4 (Task 8) |
| FR13 | Cho phép manual import dữ liệu (JSON/CSV) khi provider tự động không khả dụng | Nguyên tắc 3.3 |
| FR14 | Dữ liệu trung gian (raw, normalized, metrics, insights, benchmark, recommendation, metadata) được lưu có cấu trúc để Ver 4 tái sử dụng | Mục 5 |
| FR15 | Không gọi tập đối thủ người dùng nhập là "toàn ngành/thị trường" nếu dữ liệu không đủ đại diện | Task 6 |
| FR16 | Ver 3 đặt sau feature flag, tắt mặc định — không ảnh hưởng luồng Facebook hiện có | Task 7 |
| FR17 | Existing Ver 1 (`/api/research`, `/api/report/*`, `/api/history`) và Ver 2 (`/api/competitor/facebook`) routes giữ nguyên hành vi 100% | Nguyên tắc 3.2 |

## 6. Non-functional Requirements

| # | Yêu cầu |
|---|---|
| NFR1 | **Backward compatibility**: không đổi request/response contract của route đang chạy; API mới dùng path riêng (`/api/v3/...` hoặc `/api/benchmark/...`, xem `V3_ARCHITECTURE.md`) |
| NFR2 | **Không phụ thuộc tuyệt đối vào scraping**: mọi platform adapter phải có ít nhất 1 fallback path (manual import hoặc mock) khi provider chính không khả dụng |
| NFR3 | **Chống SSRF**: validator không thực hiện network request tới URL tuỳ ý người dùng nhập trước khi xác nhận domain nằm trong allowlist nền tảng hỗ trợ |
| NFR4 | **Data freshness**: mỗi bản ghi có `collected_at`; dashboard hiển thị rõ dữ liệu được thu thập khi nào, không ngầm định "mới nhất" |
| NFR5 | **Rate limit / cost control**: giữ nguyên nguyên tắc `FACEBOOK_POST_LIMIT`-kiểu (hard cap số bài/kênh) cho mọi platform mới, cấu hình qua `config.json`/env, không hard-code |
| NFR6 | **Data privacy**: chỉ thu thập dữ liệu công khai (không đăng nhập, không bypass privacy) — kế thừa nguyên tắc đã có ở `RISK_ANALYSIS.md` §1 |
| NFR7 | **Khả năng mở rộng Ver 4**: mọi entity mới phải có `id`, `created_at`, `updated_at`, và tham chiếu ngược được tới `research_project`/`brand`/`channel` gốc |
| NFR8 | **Test coverage**: URL validator, platform detector, mock adapter phải có unit test; test hiện có (117 test CIC) không được fail sau khi thêm code Ver 3 |
| NFR9 | **Không thêm framework/DB mới** khi chưa thật cần thiết (Nguyên tắc 7) |

## 7. Acceptance Criteria (Sprint V3.1 — chỉ áp dụng cho phần nền móng, chưa phải Ver 3 hoàn chỉnh)

1. `detect_platform()` mở rộng nhận đúng Facebook/LinkedIn/TikTok URL hợp lệ,
   từ chối domain không hỗ trợ và URL malformed — có unit test chứng minh.
2. URL validator chuẩn hoá đúng: bỏ query tracking, bỏ `/` cuối, phát hiện
   trùng lặp sau chuẩn hoá.
3. `MockAdapter` trả về `NormalizedProfile`/`NormalizedPost` hợp lệ theo đúng
   schema hiện có (test bằng `schemas/` Pydantic validation, không raise).
4. Toàn bộ 117 test hiện có của CIC vẫn pass sau khi thêm code Ver 3.
5. Ver 1 (`/api/research`, `/api/report/*`) và Ver 2 (`/api/competitor/facebook`)
   vẫn trả đúng response như trước khi có Sprint V3.1 (regression check thủ
   công bằng cách gọi lại route cũ với input mẫu).
6. Feature flag Ver 3 (`ENABLE_SOCIAL_BENCHMARK` hoặc tương đương trong
   `config.json`) mặc định tắt/không route nào của Ver 3 được mount nếu flag
   tắt.
7. Không có secret nào bị commit; `.env.example` chỉ chứa placeholder rỗng.

## 8. Error Cases cần xử lý (thiết kế, một phần implement ở skeleton)

| Tình huống | Xử lý mong đợi |
|---|---|
| URL không thuộc domain nền tảng nào được hỗ trợ | Trả lỗi 400 rõ ràng, liệt kê platform hỗ trợ, không tạo job |
| URL hợp lệ nhưng trùng với URL đã có trong cùng benchmark run | Từ chối thêm, báo "đã tồn tại trong danh sách" |
| Platform được nhận diện nhưng chưa có Adapter thật (LinkedIn/TikTok ở V3.1) | Trả trạng thái "Requires manual input" hoặc thông báo "chưa hỗ trợ thu thập tự động, dự kiến ở Sprint V3.2+", KHÔNG lỗi 500 |
| 1 trong N đối thủ thu thập thất bại | Job tiếp tục, đối thủ đó đánh dấu `Failed`/`Partially collected`, report vẫn sinh cho phần còn lại |
| LinkPower channel thu thập thất bại | Benchmark liên quan bị hạ xuống "Không đủ dữ liệu" cho phần so sánh đó (kế thừa `benchmark/rules.py` hiện có) |
| URL trỏ tới domain hợp lệ nhưng nội dung không phải trang mạng xã hội (redirect lạ) | Adapter trả `DataUnavailableError`, không network request thêm ngoài domain đã allowlist |

## 9. Data Privacy

- Chỉ thu thập dữ liệu **công khai** (không đăng nhập bằng tài khoản giả,
  không bypass checkpoint/CAPTCHA) — giữ nguyên nguyên tắc đã ghi trong
  `adapters/base.py` docstring hiện tại, áp dụng cho mọi Adapter mới.
- Không lưu thông tin định danh cá nhân (PII) của người dùng cuối (chỉ thu
  thập dữ liệu ở cấp trang/kênh, không thu thập danh sách người theo dõi
  cá nhân).
- URL do người dùng nhập không được dùng để network request ngoài phạm vi
  domain nền tảng đã allowlist (chống SSRF — xem NFR3).

## 10. Rate limit

- Mỗi platform có hard cap số bài/video thu thập mỗi kênh, cấu hình qua
  `config.json` (theo đúng pattern `facebook_post_limit` hiện có), mặc định
  đề xuất bảo thủ (≤30) cho Sprint đầu mỗi platform mới.
- Số brand/đối thủ tối đa trong 1 benchmark run cần giới hạn cấu hình được
  (đề xuất mặc định: 1 LinkPower + tối đa 5 đối thủ/run ở V3.1) để kiểm soát
  chi phí AI + provider.

## 11. Data freshness

- Mỗi `normalized_social_item`/`benchmark_result` có `collected_at` và
  `data_quality`/`collection_status` — dashboard phải hiển thị các trường
  này, không suy diễn "dữ liệu mới nhất" nếu không có timestamp.
- Không có yêu cầu real-time — đây là hệ thống phân tích theo yêu cầu
  (on-demand), không phải monitoring liên tục (đó là phạm vi
  `FUTURE_ROADMAP.md` §2 — Competitor Monitoring, ngoài phạm vi Ver 3).

## 12. Khả năng mở rộng sang Ver 4

- Mọi entity mới (xem `V3_DATA_MODEL.md`) phải cho phép truy vấn theo
  `research_project_id` + khoảng thời gian mà không cần gọi lại Adapter/AI.
- `ai_insights` và `benchmark_results` phải lưu tách biệt với `raw_social_items`
  để Ver 4 có thể tổng hợp nhiều lần chạy Ver 3 khác nhau theo thời gian
  (trend) mà không cần parse lại raw payload.
- Không entity nào của Ver 3 được phép phá vỡ 2 hợp đồng đã khoá của Ver 2:
  `PlatformAdapter` interface và `NormalizedProfile`/`NormalizedPost` schema
  (đúng nguyên tắc đã ghi ở `FUTURE_ROADMAP.md` §7 của Ver 2).
