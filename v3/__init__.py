"""v3/ - Nen mong Social Competitor Benchmark (Sprint V3.1).

Package MOI, TACH BIET hoan toan voi adapters/schemas/benchmark/engine da
"khoa kien truc" o Sprint 1-2 (xem docs/ver3/V3_ARCHITECTURE.md muc 11) -
chi IMPORT tu cac package do (vd `from schemas import Platform`), khong bao
gio bi import nguoc lai boi main.py/engine/pipeline.py hien tai. Dieu nay
dam bao Sprint V3.1 khong the pha vo Ver 1/Ver 2 dang chay production: neu
xoa nguyen package `v3/` nay, he thong Facebook MVP van chay dung 100% nhu
truoc.

- url_validator.py       - validate_url/normalize_url/ensure_no_duplicates
- platform_detector.py    - detect_platform_from_url(url) -> Platform | None
- feature_flags.py         - is_social_benchmark_enabled(config)
"""
