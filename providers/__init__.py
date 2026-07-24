"""providers/ - Client goi ra ngoai, tach khoi logic Adapter (FOLDER_STRUCTURE.md
Sprint 1 muc 2).

- facebook_extractor.py            - interface FacebookExtractor (ABC) +
  ExtractedProfile/ExtractedPost/ExtractionResult - hop dong duy nhat ma
  adapters/facebook_adapter.py phu thuoc
- facebook_apify_provider.py       - implementation THAT, MAC DINH production
  (Apify - apify/facebook-pages-scraper + apify/facebook-posts-scraper)
- facebook_playwright_provider.py  - implementation THAT thay the (Playwright
  headless Chromium, che do an danh) - CHI dung khi chu dong dat
  FACEBOOK_PROVIDER=playwright (xem registry.py), khong con la mac dinh
- facebook_fixture_provider.py     - implementation GIA LAP, CHI dung o
  tests/ - main.py KHONG import module nay
- registry.py                      - get_facebook_extractor(): chon Apify/
  Playwright dua tren FACEBOOK_PROVIDER, KHONG tu dong fallback qua lai
- ai_provider.py                   - OpenAIAIClient, implement
  analyzer.AIClient (port tu MARKET_INTELLIGENCE_CENTER/providers/ai_provider.py)
"""

from .facebook_extractor import (
    ExtractedPost,
    ExtractedProfile,
    ExtractionResult,
    ExtractionStatus,
    FacebookExtractor,
)

__all__ = [
    "FacebookExtractor",
    "ExtractedProfile",
    "ExtractedPost",
    "ExtractionResult",
    "ExtractionStatus",
]
