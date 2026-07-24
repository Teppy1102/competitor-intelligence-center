"""Interface Extractor cho Facebook - TACH RIENG khoi Mapper
(adapters/facebook_adapter.py) theo dung yeu cau: "sau nay co the thay bang
nguon du lieu ben thu ba ma khong thay doi Unified Schema hoac Analysis
Engine".

Extractor CHI biet cach doc du lieu THO tu 1 URL Facebook (bang cach nao -
Playwright, hoac sau nay Apify/Phantombuster) va tra ve dung cac dataclass o
day (ExtractedProfile/ExtractedPost/ExtractionResult) - hoan toan KHONG biet
gi ve schemas.NormalizedProfile/NormalizedPost. adapters/facebook_adapter.py
(Mapper) moi la noi doc ExtractionResult va ep ve Unified Schema.

Muon doi nguon du lieu (vd Apify) sau nay: viet 1 class moi implement
FacebookExtractor, tra dung ExtractionResult - KHONG dong gi den
facebook_adapter.py, schemas/, analyzer/, benchmark/, report/.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class ExtractionStatus(str, Enum):
    """Trang thai ket qua thu thap - KHONG bao gio duoc phep "gia lap" du
    lieu khi UNAVAILABLE/PARTIAL (yeu cau: 'tuyet doi khong tao so lieu thay
    the')."""

    OK = "ok"                    # Lay duoc du lieu day du nhu ky vong
    PARTIAL = "partial_data"     # Lay duoc mot phan (vd thieu follower count,
                                 # hoac chi lay duoc it bai hon max_posts)
    UNAVAILABLE = "data_unavailable"  # Bi chan hoan toan (login wall,
                                       # checkpoint, CAPTCHA, trang khong ton
                                       # tai/private) - KHONG co du lieu nao
                                       # doc duoc


@dataclass
class ExtractedProfile:
    """Du lieu profile THO, chua parse - Mapper (adapters/facebook_adapter.py
    + adapters/normalize.py) chiu trach nhiem parse follower_count_text/...
    thanh kieu du lieu chuan cua Unified Schema (schemas.NormalizedProfile).

    Cac field o cuoi (likes_text, rating_text, email, phone, address,
    website, categories) la du lieu THAT Facebook Pages Scraper (Apify) tra
    ve nhung Unified Schema (da khoa, khong duoc sua) KHONG co field rieng
    tuong ung - Mapper se gap chung vao NormalizedProfile.bio (van la du
    lieu that, chi la khong co o vi tri "dung" trong schema) thay vi bo di.
    Playwright provider khong dien cac field nay (None/rong) - hoan toan
    tuong thich nguoc."""

    display_name: str | None = None
    handle: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    category: str | None = None
    follower_count_text: str | None = None
    verified: bool | None = None
    fields_missing: list[str] = field(default_factory=list)

    likes_text: str | None = None
    """So Page Likes (KHAC follower_count/followers) - Facebook Pages
    Scraper tra rieng field nay. TUYET DOI khong dung de suy dien
    follower_count."""
    rating_text: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    website: str | None = None
    categories: list[str] = field(default_factory=list)


@dataclass
class ExtractedPost:
    """Du lieu 1 bai dang THO. published_at_text la chuoi hien thi tren
    trang (vd "1 giờ", "20 Tháng 3") - Mapper parse thanh datetime."""

    post_id: str
    permalink: str
    caption_text: str
    published_at_text: str | None
    type_hint: str  # "video" | "photo" | "reel" | "text" | "link" | "carousel"
    thumbnail_url: str | None = None
    media_urls: list[str] = field(default_factory=list)
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    views: int | None = None
    engagement_reliable: bool = False


@dataclass
class ExtractionResult:
    status: ExtractionStatus
    profile: ExtractedProfile | None
    posts: list[ExtractedPost]
    reason: str | None = None
    """Ly do cu the khi status != OK (vd 'Facebook yeu cau dang nhap de xem
    trang nay o che do an danh') - dua thang vao Completeness.data_gaps."""


class FacebookExtractor(ABC):
    """Interface DUY NHAT ma adapters/facebook_adapter.py phu thuoc. Khong
    import truc tiep Playwright/httpx/... o day - implementation cu the (vd
    facebook_playwright_provider.py) moi lam viec do."""

    @abstractmethod
    async def extract(self, url: str, max_posts: int) -> ExtractionResult:
        """Mo 1 phien lam viec HOAN TOAN moi (che do an danh, khong tai su
        dung cookie/session giua cac lan goi) de doc du lieu cong khai cua
        1 Fanpage. KHONG duoc co gang dang nhap/vuot CAPTCHA/checkpoint -
        neu gap, tra ExtractionResult(status=UNAVAILABLE, reason=...).
        """
        raise NotImplementedError
