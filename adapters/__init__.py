"""adapters/ - Platform Adapter layer (Competitor Intelligence Center)

Tang DUY NHAT duoc phep biet chi tiet ky thuat cua tung nen tang MXH
(ARCHITECTURE.md Sprint 1 muc 3.1). Facebook la nen tang duy nhat co
provider that trong production (MVP_SCOPE.md). Sprint V3.1 bo sung THEM
contract cho LinkedIn/TikTok (chua co provider that) + Mock/ManualImport
(dung cho test/dev/fallback) - xem docs/ver3/V3_ARCHITECTURE.md muc 5.

- base.py                 - PlatformAdapter (ABC), RawProfile, RawPost,
                             AdapterError, DataUnavailableError,
                             AdapterCapabilityError (moi - Sprint V3.1)
- registry.py              - detect_platform(url, adapters)
- normalize.py              - helper thuan ep Raw* -> Normalized* (schemas/)
- facebook_adapter.py        - FacebookAdapter (production that)
- linkedin_adapter.py          - LinkedInAdapter (moi - contract only, Sprint V3.1)
- tiktok_adapter.py              - TikTokAdapter (moi - contract only, Sprint V3.1)
- manual_import_adapter.py         - ManualImportAdapter (moi - Sprint V3.1)
- mock_adapter.py                    - MockAdapter (moi - test/dev, Sprint V3.1)
"""

from .base import (
    AdapterCapabilityError,
    AdapterError,
    DataUnavailableError,
    PlatformAdapter,
    RawPost,
    RawProfile,
)
from .facebook_adapter import FacebookAdapter
from .linkedin_adapter import LinkedInAdapter
from .manual_import_adapter import ManualImportAdapter
from .mock_adapter import MockAdapter
from .registry import detect_platform
from .tiktok_adapter import TikTokAdapter

__all__ = [
    "PlatformAdapter",
    "RawProfile",
    "RawPost",
    "AdapterError",
    "DataUnavailableError",
    "AdapterCapabilityError",
    "FacebookAdapter",
    "LinkedInAdapter",
    "TikTokAdapter",
    "ManualImportAdapter",
    "MockAdapter",
    "detect_platform",
]
