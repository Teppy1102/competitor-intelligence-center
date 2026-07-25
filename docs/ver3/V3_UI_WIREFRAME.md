# V3_UI_WIREFRAME.md — Social Competitor Benchmark (Sprint V3.1)

> Wireframe mức component, không phải giao diện hoàn chỉnh (đúng phạm vi Task
> 8 của đề bài). Phải đồng bộ với `edu.linkpower.vn/research` hiện tại —
> nghĩa là dùng lại đúng class CSS (`.card`, `.btn`, `.data-table`,
> `.progress-track`, `.badge`) và pattern IIFE module độc lập đã có ở
> `ladipage/app.js` (`App` cho Ver 1, `Cic` cho Ver 2). Sprint V3.1 **chỉ
> tạo file skeleton riêng** (`ladipage/benchmark_wireframe.js`) — **không**
> sửa `ladipage/app.js` production, để không có rủi ro nào với Ver 1/Ver 2
> đang chạy. Việc merge vào `app.js` thật là công việc của Sprint V3.2 khi
> đã có route API thật để gọi.

## 1. Vị trí trên trang

`edu.linkpower.vn/research` hiện có 2 khối độc lập theo chiều dọc: khối
`App` (Market Research) và khối `Cic` (Facebook Competitor). Ver 3 thêm khối
thứ 3 **`Benchmark`** ngay dưới khối `Cic`, cùng layout `.card`/`.mic-section-grid`
đã có — không tạo trang mới, không đổi navigation.

```
┌─────────────────────────────────────────────┐
│  Market Intelligence Research  (App module)   │  ← đã có, không đổi
├─────────────────────────────────────────────┤
│  Facebook Competitor Intelligence (Cic module)│  ← đã có, không đổi
├─────────────────────────────────────────────┤
│  Social Competitor Benchmark  (Benchmark)     │  ← MỚI — Sprint V3.1 wireframe
└─────────────────────────────────────────────┘
```

## 2. Bước 1 — Platform selector

```
┌─ Chọn nền tảng phân tích ──────────────────────┐
│  [x] Facebook   [ ] LinkedIn (sắp có)          │
│  [ ] TikTok (sắp có)                            │
│  * Có thể chọn nhiều nền tảng cùng lúc          │
└─────────────────────────────────────────────────┘
```

LinkedIn/TikTok hiển thị **disabled + nhãn "sắp có"** (không ẩn hoàn toàn —
đúng nguyên tắc "nhận diện được nhưng chưa xử lý" của `PLATFORM_STRATEGY.md`),
tooltip dùng nguyên văn `NOT_SUPPORTED_MESSAGE` từ `adapters/linkedin_adapter.py`/
`adapters/tiktok_adapter.py`.

## 3. Bước 2 — Brand & competitor URL input

```
┌─ Thương hiệu LinkPower ─────────────────────────┐
│  Nền tảng: [Facebook ▾]  URL: [___________]     │
│  [+ Thêm nền tảng khác cho LinkPower]           │
└───────────────────────────────────────────────────┘

┌─ Đối thủ ────────────────────────────────────────┐
│  #1  [Tên đối thủ____] [Facebook ▾] [URL______] ⓧ │
│  #2  [Tên đối thủ____] [TikTok ▾]   [URL______] ⓧ │
│  [+ Thêm đối thủ]   (tối đa 5 — xem NFR cấu hình) │
│  Ghi chú (tuỳ chọn): [_______________________]    │
└─────────────────────────────────────────────────────┘
```

- Validate client-side ngay khi rời khỏi ô URL (gọi tương đương
  `v3/url_validator.py` ở phía JS — regex đơn giản, backend luôn validate
  lại theo đúng nguyên tắc "không tin frontend" đã có ở `WORKFLOW.md`).
- URL trùng (theo `find_duplicate_urls`) → viền đỏ ô nhập + thông báo ngay
  tại chỗ, không cần bấm submit mới biết (đúng US2 của
  `V3_PRODUCT_REQUIREMENTS.md`).

## 4. Bước 3 — Analysis configuration

```
┌─ Cấu hình phân tích ─────────────────────────────┐
│  Số bài/kênh: [30 ▾]     Khoảng thời gian: [90 ngày ▾] │
│  Ngôn ngữ: [Tiếng Việt ▾] Mục tiêu: [Tổng quan ▾]  │
└─────────────────────────────────────────────────────┘
```

Giá trị mặc định hợp lý nếu người dùng không chọn (đúng đề bài Bước 3):
30 bài/kênh, 90 ngày, tiếng Việt, mục tiêu "Tổng quan".

## 5. Bước 4/5 — Competitor list + trạng thái thu thập

```
┌─ Danh sách kênh & trạng thái ────────────────────────┐
│  LinkPower · Facebook          ● Collected  (30/30)   │
│  Đối thủ A · Facebook          ● Collecting…           │
│  Đối thủ B · TikTok            ● Requires manual input │
│  Đối thủ C · LinkedIn          ● Failed — xem chi tiết  │
└─────────────────────────────────────────────────────────┘
```

Badge màu theo `collection_status` (`badge-green`=Collected,
`badge-blue`=Collecting, `badge-orange`=Partially collected,
`badge-gray`=Requires manual input, `badge-red`=Failed) — tái dùng đúng
class `.badge` đã có trong `style.css` hiện tại.

## 6. Job progress (loading state)

Tái dùng nguyên bản `LoadingController` pattern đã có ở `App` module
(`ladipage/app.js`) — danh sách stage tương ứng pipeline
(`V3_ARCHITECTURE.md` §3): "Đang xác thực URL" → "Đang thu thập dữ liệu
từng kênh" → "Đang chuẩn hoá & tính chỉ số" → "AI đang phân tích" → "Đang
tổng hợp Benchmark" → "Hoàn tất". Khác `Cic` (đồng bộ, chỉ 1 spinner) —
`Benchmark` cần hiển thị **tiến độ theo từng kênh** vì có N kênh song song.

## 7. Error state

```
┌─ Không thể hoàn tất 1 số kênh ───────────────────┐
│  ⚠ Đối thủ C (LinkedIn): Nền tảng LinkedIn hiện    │
│     chưa hỗ trợ thu thập tự động — dùng Manual     │
│     Import hoặc bỏ qua kênh này.                    │
│  [Tiếp tục xem Benchmark với 3/4 kênh]  [Huỷ]       │
└──────────────────────────────────────────────────────┘
```

Không chặn toàn bộ luồng — đúng FR6 (1 kênh lỗi không sập cả job).

## 8. Empty state

```
┌───────────────────────────────────────────┐
│        (icon layers)                       │
│   Chưa có Benchmark nào được chạy           │
│   Thêm đối thủ và bấm "Chạy Benchmark"       │
│   để bắt đầu so sánh với LinkPower.           │
└───────────────────────────────────────────────┘
```

## 9. Benchmark dashboard placeholder

```
┌─ Tổng quan Benchmark ────────────────────────────────┐
│  [KPI card] Share of Engagement   [KPI card] Overall  │
│  [KPI card] Content Consistency   [KPI card] ...      │
├────────────────────────────────────────────────────────┤
│  Bảng so sánh: LinkPower vs từng đối thủ (one_vs_one)  │
│  Bảng so sánh: LinkPower vs nhóm đối thủ (one_vs_group)│
│  * "So sánh dựa trên N đối thủ do người dùng nhập,      │
│     không đại diện toàn ngành" (bắt buộc hiển thị)      │
├────────────────────────────────────────────────────────┤
│  Content Pillar breakdown theo từng kênh (bar chart)    │
│  Top bài nổi bật mỗi kênh                                │
│  Recommendation / Action Plan                              │
└────────────────────────────────────────────────────────────┘
```

Tái dùng `genericTableBody()`, `barChart()`, `metricCard()` đã có sẵn trong
`Cic` module của `ladipage/app.js` (không viết lại từ đầu — chỉ gọi với dữ
liệu multi-channel).

## 10. Component skeleton (file mới, chưa merge vào `app.js`)

`ladipage/benchmark_wireframe.js` (tạo mới ở Sprint này, đứng độc lập,
**không** được `<script>` include vào trang production — chỉ là tài liệu
tham khảo implement cho Sprint V3.2 khi có API thật để gọi):

```js
/* Skeleton IIFE - Sprint V3.1 wireframe, CHUA wire API that (V3.2+) */
const Benchmark = (() => {
  function renderPlatformSelector(container, { onChange }) { /* … */ }
  function renderBrandForm(container, { onSubmit }) { /* … */ }
  function renderChannelStatusList(container, channels) { /* … */ }
  function renderErrorState(container, failedChannels, { onContinue }) { /* … */ }
  function renderEmptyState(container) { /* … */ }
  function renderDashboard(container, benchmarkRun) { /* … */ }
  return {
    renderPlatformSelector,
    renderBrandForm,
    renderChannelStatusList,
    renderErrorState,
    renderEmptyState,
    renderDashboard,
  };
})();
```

Đây là **chữ ký hàm** (contract), chưa implement thân hàm — đúng phạm vi
"wireframe/component skeleton" của Task 8, không phải giao diện hoàn chỉnh.
