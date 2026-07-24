# PRODUCTION_ACCEPTANCE_CHECKLIST.md — Nghiệm thu MVP Facebook (Apify)

> Dùng checklist này để xác nhận trước khi công bố nội bộ. Đánh dấu từng mục
> sau khi tự kiểm tra — không đánh dấu nếu chưa verify thật (đặc biệt các
> mục cần token Apify thật).

## A. Cấu hình & bảo mật

- [ ] `.env` tồn tại, chứa `APIFY_API_TOKEN` thật (kiểm tra bằng
      `sed -E 's/=.*/=<redacted>/' .env`, KHÔNG dùng `cat .env`).
- [ ] `.gitignore` có `.env`, `.env.*`, `!.env.example`.
- [ ] `git status` (sau `git init`) xác nhận `.env` **không** xuất hiện trong
      danh sách file sẽ commit.
- [ ] Không có token xuất hiện trong bất kỳ file `.py`/`.md`/`.json` nào
      (`grep -rn "apify_api" --include=*.py --include=*.md .` chỉ nên thấy
      tên biến, không thấy giá trị thật).
- [ ] Log ứng dụng (`cic.facebook_apify`, `cic.pipeline`, `cic.main`) không
      in giá trị token — chỉ in độ dài/trạng thái có/không (xem
      `scripts/smoke_test_apify.py::_mask_token_status()` làm ví dụ).

## B. Provider & Registry

- [ ] `FACEBOOK_PROVIDER` mặc định là `apify` khi không đặt biến môi trường
      (`tests/test_providers/test_registry.py::test_default_provider_is_apify_when_env_unset`).
- [ ] `main.py` không import `providers.facebook_playwright_provider` hay
      `providers.facebook_fixture_provider` ở cấp module
      (`grep -n "^from providers" main.py`).
- [ ] Playwright không được import vào `sys.modules` khi chạy với
      `FACEBOOK_PROVIDER=apify`
      (`tests/test_providers/test_registry.py::test_playwright_module_not_imported_when_provider_is_apify`).
- [ ] Không có cơ chế tự động fallback Apify → Playwright hoặc → Fixture ở
      bất kỳ đâu trong `main.py`/`providers/registry.py`.

## C. Giới hạn 30 bài & bỏ time_range

- [ ] `providers/facebook_apify_provider.FACEBOOK_POST_LIMIT == 30`.
- [ ] `APIFY_MAX_POSTS` đặt cao hơn 30 vẫn bị hard-cap về 30
      (`test_apify_max_posts_env_is_hard_capped_at_30`).
- [ ] Request có `time_range` (kể cả giá trị không hợp lệ) không làm request
      thất bại và không ảnh hưởng kết quả
      (`test_pipeline_never_fails_on_deprecated_time_range_value`,
      `test_pipeline_result_identical_with_or_without_deprecated_time_range`).
- [ ] Frontend (`ladipage/`) không còn bộ chọn 1/3/6 tháng, không gửi
      `time_range` (`tests/test_frontend/`).

## D. Chống bịa dữ liệu (Partial data)

- [ ] Pages OK + Posts OK → pipeline chạy bình thường, báo đúng số bài thật.
- [ ] Pages OK + Posts fail → giữ metadata Fanpage, không tạo bài viết giả.
- [ ] Posts OK + Pages fail → giữ bài viết, không tạo tên Fanpage/follower giả
      (hiển thị `"(Không rõ tên trang)"`).
- [ ] Cả hai fail/Dataset rỗng → trả lỗi rõ ràng (`data_unavailable`), không
      gọi AI sinh báo cáo như có dữ liệu thật.
- [ ] Fanpage < 30 bài → hiển thị đúng số thật (vd 17), không hiển thị 30.

## E. Test tự động

- [ ] `python -m pytest -q` — toàn bộ pass, không skip ngầm.
- [ ] Không có test nào gọi Apify thật (`grep -rn "console.apify.com\|ApifyClient(" tests/`
      chỉ nên thấy `FakeApifyClientAsync`, không thấy `ApifyClientAsync(` thật).

## F. Smoke test thật (cần token Apify thật)

- [ ] Chạy `python scripts/smoke_test_apify.py https://www.facebook.com/LinkPowerVN`.
- [ ] Xác nhận tên field thực tế trong Dataset khớp (hoặc đã cập nhật lại
      candidate key trong `facebook_apify_provider.py` nếu khác) — xem
      `APIFY_SETUP_AND_TEST.md` mục 4.
- [ ] Xác nhận `data_status` phản ánh đúng thực tế (không luôn là "complete").

## G. Endpoint & Frontend

- [ ] Route vẫn là `POST /api/competitor/facebook` — không đổi.
- [ ] Response JSON vẫn tương thích cấu trúc `CompetitorReport` cũ (13 section
      + các field bổ sung `posts_analyzed`/`posts_requested_limit`/`data_status`).
- [ ] `ladipage/ladipage_embed.html` đã được tạo lại SAU cùng (build cuối) từ
      `index.html`/`style.css`/`app.js` mới nhất.

## H. Chi phí & vận hành

- [ ] Log Actor run ID, status, duration, usage_usd cho mỗi lần phân tích
      (`cic.facebook_apify` logger).
- [ ] Đã đọc và hiểu ước tính chi phí Apify (xem `DATA_SOURCE_DESIGN.md` §6 —
      áp dụng tương tự, cần cập nhật số liệu thật sau khi chạy vài chục
      request thật).
- [ ] Đã xác nhận Render dùng gói `free` (không cần Chromium) hoặc gói phù hợp
      nếu có kế hoạch bật lại Playwright.
