"""adapters/ - Platform Adapter layer (Competitor Intelligence Center)

Tang DUY NHAT duoc phep biet chi tiet ky thuat cua tung nen tang MXH
(ARCHITECTURE.md Sprint 1 muc 3.1). Sprint nay (bo sung sau Sprint 2) trien
khai Facebook - nen tang duy nhat trong pham vi MVP hien tai (MVP_SCOPE.md).

- base.py       - PlatformAdapter (ABC), RawProfile, RawPost, AdapterError
- registry.py   - detect_platform(url, adapters)
- normalize.py  - helper thuan ep Raw* -> Normalized* (schemas/)
- facebook_adapter.py - FacebookAdapter (Mapper, nhan FacebookExtractor qua DI)
"""

from .base import AdapterError, DataUnavailableError, PlatformAdapter, RawPost, RawProfile
from .facebook_adapter import FacebookAdapter
from .registry import detect_platform

__all__ = [
    "PlatformAdapter",
    "RawProfile",
    "RawPost",
    "AdapterError",
    "DataUnavailableError",
    "FacebookAdapter",
    "detect_platform",
]
