# Competitor Intelligence Center — Module 2 của LinkPower AI

> **Cập nhật trạng thái (mới nhất):** MVP Facebook đã có code chạy được
> (`schemas/`, `analyzer/`, `benchmark/`, `report/`, `adapters/`, `providers/`,
> `engine/`, `main.py`, frontend tại `ladipage/`). Facebook Provider production
> **mặc định là Apify** (`apify/facebook-pages-scraper` + `apify/facebook-posts-scraper`)
> — Playwright vẫn còn trong source code làm lựa chọn thủ công
> (`FACEBOOK_PROVIDER=playwright`), không còn là mặc định vì Facebook giới hạn
> dữ liệu xem ẩn danh. MVP hiện chỉ phân tích **tối đa 30 bài viết gần nhất**,
> không còn khái niệm khoảng thời gian 1/3/6 tháng. Xem `APIFY_SETUP_AND_TEST.md`,
> `DEPLOY_MVP_FACEBOOK.md`, `PRODUCTION_ACCEPTANCE_CHECKLIST.md` cho quy trình
> vận hành mới nhất. Phần nội dung bên dưới là tài liệu Sprint 1 gốc (giữ
> nguyên làm hồ sơ quyết định kiến trúc, một số chi tiết — vd Facebook qua
> "third-party data provider" chưa chọn, khoảng thời gian 1/3/6 tháng — nay đã
> được cụ thể hoá/thay đổi như trên).
>
> **Trạng thái Sprint 1: Architecture First — hoàn thành và ĐÃ DUYỆT.**

## Đây là gì?

Module thứ 2 trong hệ sinh thái LinkPower AI, đứng cạnh **Market Intelligence Center** (đã deploy tại `edu.linkpower.vn/research`). Trong khi MIC nghiên cứu **một thị trường/từ khoá**, Competitor Intelligence Center (CIC) nghiên cứu **một đối thủ cụ thể** qua URL Facebook/LinkedIn/YouTube/TikTok của họ, trong khoảng thời gian 1/3/6 tháng, và trả về báo cáo 13 phần bao gồm Benchmark trực tiếp với LinkPower.

## Mục lục 10 tài liệu Sprint 1

| # | Tài liệu | Nội dung chính |
|---|---|---|
| 1 | [ARCHITECTURE.md](./ARCHITECTURE.md) | Kiến trúc tổng thể — Adapter Pattern + Normalized Schema, lý do đây là quyết định quan trọng nhất |
| 2 | [WORKFLOW.md](./WORKFLOW.md) | Luồng xử lý end-to-end từ lúc user dán URL đến khi có report |
| 3 | [FOLDER_STRUCTURE.md](./FOLDER_STRUCTURE.md) | Cấu trúc thư mục source code cho Sprint 2, `config.json` với URL LinkPower thật |
| 4 | [REPORT_SPECIFICATION_V1.md](./REPORT_SPECIFICATION_V1.md) | Spec chi tiết 13 section report + JSON schema + quy tắc chống bịa dữ liệu |
| 5 | [PROMPT_DESIGN.md](./PROMPT_DESIGN.md) | Cấu trúc prompt AI, chiến lược chọn bài viết đưa vào prompt, versioning |
| 6 | [DATA_SOURCE_DESIGN.md](./DATA_SOURCE_DESIGN.md) | **Tài liệu quan trọng nhất về khả thi** — đánh giá nguồn dữ liệu từng nền tảng + ước tính ngân sách Facebook |
| 7 | [PLATFORM_STRATEGY.md](./PLATFORM_STRATEGY.md) | Thứ tự triển khai nền tảng — **Facebook trước** theo quyết định LinkPower |
| 8 | [RISK_ANALYSIS.md](./RISK_ANALYSIS.md) | Rủi ro pháp lý/ToS, dữ liệu, chi phí, kỹ thuật, AI, kỳ vọng người dùng |
| 9 | [MVP_SCOPE.md](./MVP_SCOPE.md) | Phạm vi MVP: Facebook + URL LinkPower thật, Definition of Done |
| 10 | [FUTURE_ROADMAP.md](./FUTURE_ROADMAP.md) | Hướng mở rộng sau MVP: Monitoring, Market Alert, Website Intelligence, tích hợp platform chung |

## Tóm tắt điều hành (Executive Summary)

**Quyết định kiến trúc cốt lõi:** Tách biệt hoàn toàn tầng thu thập dữ liệu theo nền tảng (Adapter) khỏi tầng phân tích AI, thông qua 1 schema dữ liệu chuẩn hoá duy nhất. Đây là điều kiện bắt buộc để đáp ứng yêu cầu "reusable, không hardcode riêng Facebook" trong đề bài gốc.

**Phát hiện quan trọng cần lưu ý khi vận hành:** Không giống Market Intelligence Center (dữ liệu tìm kiếm mở, dễ lấy), 3 trong 4 nền tảng yêu cầu (Facebook, LinkedIn, TikTok) **không có API chính thức phù hợp** để phân tích trang của đối thủ (bên không sở hữu). Giải pháp là dùng dữ liệu công khai qua bên thứ 3, đi kèm chi phí và rủi ro về Điều khoản Dịch vụ ở mức trung bình đến cao (LinkedIn cao nhất — vẫn tạm hoãn). Chi tiết đầy đủ ở `DATA_SOURCE_DESIGN.md` và `RISK_ANALYSIS.md` §1.

**Quyết định MVP đã chốt:** LinkPower ưu tiên **Facebook** làm nền tảng launch đầu tiên (đảo ngược đề xuất kỹ thuật ban đầu — vốn đề xuất YouTube trước vì rủi ro/chi phí thấp hơn), do giá trị kinh doanh cao hơn cho ngành đào tạo B2B. YouTube làm cùng/ngay sau vì chi phí gần bằng 0. TikTok ở giai đoạn 2, LinkedIn tạm hoãn do rủi ro pháp lý cao nhất.

## Quyết định đã duyệt (chốt sau khi LinkPower phản hồi 3 câu hỏi Sprint 1)

| # | Câu hỏi | Quyết định |
|---|---|---|
| 1 | Nền tảng launch đầu tiên | ✅ **Facebook** (nếu chỉ chọn 1) |
| 2 | Ngân sách data provider | ✅ Duyệt nguyên tắc **$40-130/tháng** cho Facebook (ước tính, xem cách tính ở `DATA_SOURCE_DESIGN.md` §6) — **cần PoC Sprint 2** xác nhận số liệu chính xác trước khi ký hợp đồng |
| 3 | URL chính thức LinkPower (4/4 nền tảng) | ✅ Facebook: `facebook.com/LinkPowerVN` · YouTube: `youtube.com/@LinkPower` · TikTok: `tiktok.com/@linkpower.vn` · LinkedIn: `vn.linkedin.com/company/linkpowervn` |

Cả 3 quyết định đã được cập nhật xuyên suốt vào `ARCHITECTURE.md` §9, `MVP_SCOPE.md` §5, `PLATFORM_STRATEGY.md` §1-2, `DATA_SOURCE_DESIGN.md` §3+§6-7, `FOLDER_STRUCTURE.md` §3 (`config.json`), và `RISK_ANALYSIS.md` §3 — không có mâu thuẫn giữa các tài liệu.

## Kế hoạch hành động (theo đúng Sprint Planning gốc)

| Sprint | Nội dung | Trạng thái |
|---|---|---|
| **Sprint 1** | Architecture, Report Spec, Workflow, Prompt Design, MVP Definition | ✅ Hoàn thành + đã duyệt |
| **Sprint 2** | Backend, Data Collection (**Facebook Adapter** — ưu tiên, + YouTube Adapter nếu kịp), Analysis Engine | 🔜 Sẵn sàng bắt đầu |
| Sprint 3 | Frontend, Dashboard, Visualization | Chờ Sprint 2 |
| Sprint 4 | Testing, Audit, Optimization | Chờ Sprint 3 |
| Sprint 5 | Deploy, Production, Documentation | Chờ Sprint 4 |

## Việc cần làm ngay khi bắt đầu Sprint 2

- [ ] PoC so sánh 2-3 data provider Facebook (Apify/Phantombuster/tương đương) — xác nhận chi phí thực tế so với ước tính $40-130/tháng ở `DATA_SOURCE_DESIGN.md` §6
- [ ] Chọn provider chính thức, tạo tài khoản, lấy API key → `.env`
- [ ] Implement `schemas/` (Pydantic models) trước tiên, theo đúng `ARCHITECTURE.md` §5
- [ ] Implement `adapters/facebook_adapter.py` — nền tảng ưu tiên số 1
- [ ] Implement `adapters/youtube_adapter.py` song song nếu thời gian cho phép (chi phí thấp, không cần chờ PoC provider)
- [ ] Test Adapter với chính Fanpage LinkPower (`facebook.com/LinkPowerVN`) trước — vừa là dữ liệu thật, vừa không có rủi ro "phân tích nhầm đối thủ nhạy cảm" trong giai đoạn dev

## Câu hỏi còn mở (không chặn Sprint 2, xử lý khi tới)

1. Ngân sách/provider cho TikTok (Giai đoạn 2) — nhắc lại khi Facebook Adapter gần hoàn thành.
2. Phương án LinkedIn an toàn hơn — chưa có, theo dõi theo `FUTURE_ROADMAP.md` §1.
