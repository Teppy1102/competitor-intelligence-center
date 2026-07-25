"""PlatformAdapter - interface trung tam theo ARCHITECTURE.md (Sprint 1) muc 4.

Day la hop dong DUY NHAT ma phan con lai cua he thong (engine/pipeline.py)
duoc phep goi de lay du lieu tho tu 1 nen tang MXH. Adapter cu the (vd
FacebookAdapter) tu quyet dinh nguon du lieu that (provider) va cach ep ve
RawProfile/RawPost - day la "ranh gioi rui ro" duy nhat, khong ro ri sang
schemas/, analyzer/, benchmark/, report/ (da lock kien truc o Sprint 1-2).

RawProfile/RawPost o day la trung gian THO (chua qua normalize) - KHAC voi
schemas.NormalizedProfile/NormalizedPost. Muc dich tach lam 2 buoc (extractor
-> Raw* -> normalize() -> Normalized*) la de sau nay thay nguon du lieu (vd
Apify/Phantombuster thay cho Playwright scraper) chi can doi ham extract,
khong doi logic normalize/mapper.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class RawProfile:
    """Du lieu tho ve 1 trang/kenh, TRUOC KHI ep ve NormalizedProfile.

    Field co the None neu Adapter khong lay duoc - KHONG suy dien gia tri
    thay the (dung nguyen tac chong bia du lieu, xem ARCHITECTURE.md muc 5.1).
    """

    source_url: str
    display_name: str
    handle: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    category: str | None = None
    follower_count: int | None = None
    verified: bool | None = None
    created_at: date | None = None

    # True neu Adapter tin day la du lieu day du/chinh xac (vd lay duoc het
    # field chinh); False neu chi lay duoc mot phan - dung de tinh
    # profile_data_confidence o normalize.py.
    fields_missing: list[str] = field(default_factory=list)


@dataclass
class RawPost:
    """Du lieu tho ve 1 bai dang, TRUOC KHI ep ve NormalizedPost."""

    post_id: str
    published_at: datetime | None
    post_type_hint: str  # "video" | "photo" | "reel" | "text" | "link" | "carousel" | "unknown"
    caption_text: str
    permalink: str
    thumbnail_url: str | None = None
    media_urls: list[str] = field(default_factory=list)
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    views: int | None = None
    # True neu Adapter tin cac so lieu engagement o tren la doc duoc ro rang
    # tu trang (khong phai doan/uoc luong) - dung de tinh engagement_confidence.
    engagement_reliable: bool = False

    # Sprint V3.2 - 2 field optional MOI, chi TikTok dung that (Facebook
    # khong co khai niem nay nen luon None) - them field optional KHONG pha
    # vo Adapter/test hien co (dataclass, khong phai Pydantic extra="forbid").
    save_count: int | None = None
    duration_seconds: int | None = None

    # Sprint V3.3.2 - JSON goc (chua qua mapping) tu Actor/API cua provider,
    # neu co - dung de collection_service.py luu vao raw_items.raw_payload
    # TRUOC KHI normalize (de bai muc 10 "Luu raw payload truoc khi
    # normalize"), giu du object long nhau (vd LinkedIn: author/engagement/
    # header/contentAttributes/postImages) ma cac field phang o tren khong
    # the hien het. None neu provider khong co JSON goc (vd Manual Import/
    # Mock) - khong bat buoc, field optional them KHONG pha vo Adapter/test
    # hien co (giong 2 field tren).
    raw_source_item: dict | None = None


class AdapterError(RuntimeError):
    """Loi chung khi Adapter khong the hoan tat yeu cau - vd URL khong hop
    le, trang khong ton tai/private. Router (main.py) bat loi nay va tra ve
    HTTP error co y nghia cho nguoi dung, KHONG phai loi 500 chung chung
    (WORKFLOW.md Sprint 1 muc 3, Luong loi)."""


class DataUnavailableError(AdapterError):
    """Nguon du lieu (vd Facebook) chan truy cap (login wall/checkpoint/
    CAPTCHA) hoac khong hien du lieu cong khai nao doc duoc - KHAC voi loi he
    thong (timeout/bug). Router tra thong bao ro rang cho nguoi dung, KHONG
    bao gio fallback sang du lieu bia/gia lap (yeu cau nguoi dung: 'tuyet doi
    khong tao so lieu thay the')."""


class AdapterCapabilityError(AdapterError):
    """Sprint V3.1 (V3_ARCHITECTURE.md muc 5/8) - KHAC voi DataUnavailableError:
    dung khi 1 nen tang DA duoc nhan dien qua detect() (vd LinkedIn/TikTok)
    nhung Adapter CHUA co provider thu that o Sprint nay (contract-only).
    Router/pipeline bat loi nay va danh dau CollectionJob.status =
    "requires_manual_input" cho DUNG channel do, KHONG chan cac channel khac
    trong cung 1 benchmark run (PLATFORM_STRATEGY.md muc 3: 'tra loi ro rang
    va dung ngu nghia', khong phai loi ky thuat kho hieu)."""


class PlatformAdapter(ABC):
    """Xem ARCHITECTURE.md (Sprint 1) muc 4. Adapter TUYET DOI khong duoc
    dang nhap/vuot CAPTCHA/checkpoint - chi doc du lieu dang hien thi cong
    khai (yeu cau nguoi dung o Sprint nay)."""

    @abstractmethod
    def detect(self, url: str) -> bool:
        """Tra True neu URL thuoc nen tang nay (dung cho registry.py)."""
        raise NotImplementedError

    @abstractmethod
    async def resolve_profile(self, url: str) -> RawProfile:
        """Lay thong tin co ban cua trang/kenh. Phai raise DataUnavailableError
        (khong phai tra gia tri gia) neu bi chan/khong doc duoc."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_posts(
        self, profile_ref: str, since: date, until: date, max_posts: int
    ) -> list[RawPost]:
        """Lay danh sach bai dang cong khai trong khoang [since, until], toi
        da max_posts bai. Tra list rong (KHONG raise) neu trang ton tai
        nhung khong co bai nao doc duoc - de pipeline con chay tiep voi
        completeness thap, dung nguyen tac 'fail gracefully theo tung phan'
        (ARCHITECTURE.md muc 2.5). Chi raise DataUnavailableError neu BAN THAN
        viec truy cap trang bi chan hoan toan (vd redirect login wall)."""
        raise NotImplementedError
