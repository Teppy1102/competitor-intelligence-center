"""ApifyFacebookExtractor - FacebookExtractor implementation THAT dung Apify
(apify-client chinh thuc) - nguon du lieu production MAC DINH cho Facebook ke
tu quyet dinh nay (thay Playwright, van giu Playwright trong source code lam
lua chon thu cong - xem providers/registry.py).

Goi DUNG 2 Actor chinh thuc:
  - APIFY_FACEBOOK_PAGES_ACTOR (mac dinh apify/facebook-pages-scraper)
  - APIFY_FACEBOOK_POSTS_ACTOR (mac dinh apify/facebook-posts-scraper)

Moi lan extract() chi tao DUNG 1 run cho moi Actor (khong retry-loop, khong
run thua) - xem _call_actor_once() cho quy tac retry (CHI retry 1 lan cho
loi mang/server tam thoi, KHONG retry input sai/dataset rong/actor that bai).

File nay CHI chiu trach nhiem: goi Actor, theo doi trang thai, doc Dataset,
parse raw response, tra ExtractionResult (ExtractedProfile/ExtractedPost) cho
FacebookAdapter (adapters/facebook_adapter.py) - KHONG phan tich Content
Pillar/Hook/CTA, KHONG tinh Benchmark, KHONG sinh AI report (dung nguyen tac
tach lop da chot - xem docstring providers/facebook_extractor.py).
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Any

from apify_client import ApifyClientAsync
from apify_client.errors import (
    ApifyApiError,
    ForbiddenError,
    InvalidRequestError,
    InvalidResponseBodyError,
    NotFoundError,
    ServerError,
    UnauthorizedError,
)

from .facebook_extractor import (
    ExtractedPost,
    ExtractedProfile,
    ExtractionResult,
    ExtractionStatus,
    FacebookExtractor,
)

logger = logging.getLogger("cic.facebook_apify")

FACEBOOK_POST_LIMIT = 30
"""Gia tri co dinh cho MVP (Muc 5 yeu cau bo sung) - HARD CAP bat ke
APIFY_MAX_POSTS/max_posts truyen vao lon hon bao nhieu, khong bao gio vuot
qua so nay o production."""

DEFAULT_PAGES_ACTOR = "apify/facebook-pages-scraper"
DEFAULT_POSTS_ACTOR = "apify/facebook-posts-scraper"
DEFAULT_TIMEOUT_SECONDS = 180

# Loi HTTP duoc coi la "tam thoi" - dang retry duoc DUNG 1 LAN THEM (apify-client
# tu no da retry noi bo cho 429/5xx/parse-loi truoc khi nem loi nay ra ngoai -
# xem apify_client/errors.py - nen day la lop retry BO SUNG, khong phai lop
# retry duy nhat).
_RETRYABLE_ERRORS = (ServerError, InvalidResponseBodyError, TimeoutError, ConnectionError, OSError)
# Loi "input sai"/tai khoan - KHONG duoc retry (yeu cau: "Khong retry input sai").
_NON_RETRYABLE_ERRORS = (InvalidRequestError, UnauthorizedError, ForbiddenError, NotFoundError)


@dataclass(frozen=True)
class _ActorRunOutcome:
    items: list[dict[str, Any]]
    error: str | None
    run_id: str | None
    usage_usd: float | None


class ApifyFacebookExtractor(FacebookExtractor):
    def __init__(
        self,
        *,
        api_token: str,
        pages_actor_id: str = DEFAULT_PAGES_ACTOR,
        posts_actor_id: str = DEFAULT_POSTS_ACTOR,
        max_posts: int = FACEBOOK_POST_LIMIT,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_total_charge_usd: Decimal | None = None,
        client: Any = None,
    ) -> None:
        if not api_token:
            raise RuntimeError(
                "Thiếu APIFY_API_TOKEN. Thêm dòng APIFY_API_TOKEN=... vào file .env "
                "(xem APIFY_SETUP_AND_TEST.md)."
            )
        # `client` cho phep tests/ inject 1 mock ApifyClientAsync - production
        # (providers/registry.py) khong bao gio truyen tham so nay, luon tao
        # client that.
        self._client = client if client is not None else ApifyClientAsync(api_token)
        self._pages_actor_id = pages_actor_id
        self._posts_actor_id = posts_actor_id
        # Hard cap - khong bao gio vuot FACEBOOK_POST_LIMIT du config/env dat cao hon.
        self._max_posts = min(max_posts, FACEBOOK_POST_LIMIT)
        self._timeout_seconds = timeout_seconds
        self._max_total_charge_usd = max_total_charge_usd

    async def extract(self, url: str, max_posts: int) -> ExtractionResult:
        effective_max = min(max_posts, self._max_posts, FACEBOOK_POST_LIMIT)

        # 1 run Pages + 1 run Posts, chay song song (khong phai run thua - moi
        # Actor van chi goi DUNG 1 lan, chi la khong cho tuan tu cho nhanh hon).
        pages_task = asyncio.create_task(self._run_pages_actor(url))
        posts_task = asyncio.create_task(self._run_posts_actor(url, effective_max))
        pages_outcome, posts_outcome = await asyncio.gather(pages_task, posts_task)

        profile = self._map_profile(pages_outcome.items) if pages_outcome.items else None
        posts = self._map_and_finalize_posts(posts_outcome.items, effective_max)

        return self._build_result(
            profile=profile,
            posts=posts,
            effective_max=effective_max,
            profile_error=pages_outcome.error,
            posts_error=posts_outcome.error,
        )

    # ------------------------------------------------------------------
    # Actor orchestration (Muc 6 + Muc 15 - kiem soat chi phi)
    # ------------------------------------------------------------------

    async def _run_pages_actor(self, url: str) -> _ActorRunOutcome:
        run_input = {"startUrls": [{"url": url}]}
        return await self._call_actor_once(
            actor_id=self._pages_actor_id, run_input=run_input, max_items=1, label="pages"
        )

    async def _run_posts_actor(self, url: str, max_posts: int) -> _ActorRunOutcome:
        # "resultsLimit" la ten field pho bien cua cac Actor Facebook cua Apify
        # cho so luong bai toi da - can xac nhan lai qua smoke test that neu
        # Actor cu the dang dung ten khac (xem APIFY_SETUP_AND_TEST.md).
        # max_items la co che GIOI HAN CUNG cua chinh Apify platform (khong
        # phu thuoc dung dung ten field input hay khong) - day la lop bao ve
        # THUC SU cho gioi han 30 bai/kiem soat chi phi.
        run_input = {"startUrls": [{"url": url}], "resultsLimit": max_posts}
        return await self._call_actor_once(
            actor_id=self._posts_actor_id, run_input=run_input, max_items=max_posts, label="posts"
        )

    async def _call_actor_once(
        self, *, actor_id: str, run_input: dict[str, Any], max_items: int, label: str
    ) -> _ActorRunOutcome:
        attempts_allowed = 2  # 1 lan chinh + TOI DA 1 lan retry cho loi mang tam thoi
        last_error: str | None = None

        for attempt in range(1, attempts_allowed + 1):
            started_at = time.monotonic()
            try:
                run = await asyncio.wait_for(
                    self._client.actor(actor_id).call(
                        run_input=run_input,
                        max_items=max_items,
                        max_total_charge_usd=self._max_total_charge_usd,
                        run_timeout=None,
                        # apify_client.types.Timeout = timedelta | Literal[...] -
                        # KHONG duoc truyen so nguyen tho (gay loi "'<' not
                        # supported between instances of 'datetime.timedelta'
                        # and 'int'" khi client so sanh noi bo). Da xac nhan
                        # bang cach doc thang source cua apify_client.
                        timeout=timedelta(seconds=self._timeout_seconds),
                    ),
                    timeout=self._timeout_seconds,
                )
            except _NON_RETRYABLE_ERRORS as exc:
                logger.warning(
                    "apify_actor_input_error label=%s actor=%s status=%s attempt=%s",
                    label, actor_id, getattr(exc, "status_code", "?"), attempt,
                )
                return _ActorRunOutcome([], f"Lỗi cấu hình/quyền truy cập Apify ({label}): {exc}", None, None)
            except _RETRYABLE_ERRORS as exc:
                last_error = f"Lỗi mạng/máy chủ Apify tạm thời ({label}): {exc}"
                logger.warning(
                    "apify_actor_transient_error label=%s actor=%s attempt=%s detail=%s",
                    label, actor_id, attempt, exc,
                )
                if attempt < attempts_allowed:
                    await asyncio.sleep(1.5)
                    continue
                return _ActorRunOutcome([], last_error, None, None)
            except asyncio.TimeoutError:
                logger.warning("apify_actor_timeout label=%s actor=%s attempt=%s", label, actor_id, attempt)
                return _ActorRunOutcome(
                    [], f"Hết thời gian chờ Actor {label} (>{self._timeout_seconds}s).", None, None
                )
            except ApifyApiError as exc:
                logger.warning(
                    "apify_actor_api_error label=%s actor=%s status=%s attempt=%s",
                    label, actor_id, getattr(exc, "status_code", "?"), attempt,
                )
                return _ActorRunOutcome([], f"Lỗi Apify API ({label}): {exc}", None, None)

            duration_s = round(time.monotonic() - started_at, 2)
            run_id = getattr(run, "id", None)
            status = getattr(run, "status", None)
            usage_usd = float(getattr(run, "usage_total_usd", 0) or 0) or None
            dataset_id = getattr(run, "default_dataset_id", None)

            logger.info(
                "apify_run_finished label=%s actor=%s run_id=%s status=%s duration_s=%s usage_usd=%s",
                label, actor_id, run_id, status, duration_s, usage_usd,
            )

            if status != "SUCCEEDED":
                # Actor chay xong nhung that bai (FAILED/ABORTED/TIMED-OUT) -
                # KHONG retry (yeu cau: "Khong retry Actor run qua mot lan" +
                # day khong phai loi mang tam thoi).
                return _ActorRunOutcome(
                    [], f"Actor {label} kết thúc với trạng thái {status}.", run_id, usage_usd
                )

            if not dataset_id:
                return _ActorRunOutcome([], f"Actor {label} không trả Dataset.", run_id, usage_usd)

            try:
                page = await self._client.dataset(dataset_id).list_items(limit=max_items)
            except ApifyApiError as exc:
                return _ActorRunOutcome([], f"Không đọc được Dataset ({label}): {exc}", run_id, usage_usd)

            items = page.items or []
            logger.info("apify_dataset_read label=%s run_id=%s item_count=%s", label, run_id, len(items))
            # Dataset rong - KHONG retry (yeu cau: "Khong retry Dataset rong"),
            # tra ve rong de _build_result() tu quyet dinh partial/unavailable.
            return _ActorRunOutcome(items, None, run_id, usage_usd)

        return _ActorRunOutcome([], last_error, None, None)

    # ------------------------------------------------------------------
    # Mapping - CHI parse raw response, KHONG phan tich/danh gia
    # ------------------------------------------------------------------

    @staticmethod
    def _map_profile(items: list[dict[str, Any]]) -> ExtractedProfile | None:
        if not items:
            return None
        item = items[0]

        title = _first_present(item, "title", "pageName", "name")
        if not title:
            return None  # khong co ten trang -> khong coi la profile hop le

        fields_missing: list[str] = []

        categories_raw = _first_present(item, "categories", "pageCategories", "category")
        categories = _as_string_list(categories_raw)
        if not categories:
            fields_missing.append("category")

        followers_raw = _first_present(item, "followers", "followersCount", "followersCountText")
        if followers_raw is None:
            fields_missing.append("follower_count")

        likes_raw = _first_present(item, "likes", "pageLikes", "likesCount")

        avatar = _first_present(
            item, "profilePictureUrl", "profilePhoto", "pictureUrl", "avatarUrl", "coverPhotoUrl"
        )
        if not avatar:
            fields_missing.append("avatar_url")

        info_raw = _first_present(item, "info", "pageInfo", "about", "intro")
        bio = _as_text(info_raw)
        if not bio:
            fields_missing.append("bio")

        email = _first_present(item, "email", "pageEmail")
        if isinstance(email, list):
            email = email[0] if email else None

        phone = _first_present(item, "phone", "pagePhone")
        if isinstance(phone, list):
            phone = phone[0] if phone else None

        website = _first_present(item, "website", "pageWebsite")
        if isinstance(website, list):
            website = website[0] if website else None

        address = _first_present(item, "address", "pageAddress", "location")
        if isinstance(address, dict):
            address = address.get("address") or address.get("street") or None

        rating = _first_present(item, "rating", "pageRating", "ratingText", "overallStarRating")

        verified = _first_present(item, "verified", "isVerified", "pageVerified")

        return ExtractedProfile(
            display_name=str(title),
            handle=None,
            avatar_url=str(avatar) if avatar else None,
            bio=bio,
            category=", ".join(categories) if categories else None,
            follower_count_text=str(followers_raw) if followers_raw is not None else None,
            verified=bool(verified) if verified is not None else None,
            fields_missing=fields_missing,
            likes_text=str(likes_raw) if likes_raw is not None else None,
            rating_text=str(rating) if rating is not None else None,
            email=str(email) if email else None,
            phone=str(phone) if phone else None,
            address=str(address) if address else None,
            website=str(website) if website else None,
            categories=categories,
        )

    @staticmethod
    def _map_post(item: dict[str, Any]) -> ExtractedPost | None:
        permalink = _first_present(item, "url", "postUrl", "topLevelUrl", "link")
        post_id = _first_present(item, "postId", "id", "facebookId", "legacyId")
        if not permalink and not post_id:
            return None  # khong co ca URL lan ID -> khong the coi la 1 bai dang hop le

        permalink = str(permalink) if permalink else ""
        post_id = str(post_id) if post_id else permalink

        text = _first_present(item, "text", "message", "caption") or ""

        published_raw = _first_present(
            item, "time", "date", "timestamp", "publishedAt", "postDate", "createdTime"
        )
        published_at_text = str(published_raw) if published_raw is not None else None

        is_video = bool(_first_present(item, "isVideo", "video")) or bool(item.get("videoUrl"))
        type_hint = "video" if is_video else "text"
        if "/reel" in permalink:
            type_hint = "reel"
        elif "/photos/" in permalink or "/photo.php" in permalink:
            type_hint = "photo"

        media_urls = _extract_media_urls(item)
        thumbnail_url = media_urls[0] if media_urls else None

        likes = _to_int(_extract_reactions_total(item))
        comments = _to_int(_first_present(item, "comments", "commentsCount"))
        shares = _to_int(_first_present(item, "shares", "sharesCount"))

        engagement_reliable = likes is not None or comments is not None or shares is not None

        return ExtractedPost(
            post_id=post_id,
            permalink=permalink,
            caption_text=str(text),
            published_at_text=published_at_text,
            type_hint=type_hint,
            thumbnail_url=thumbnail_url,
            media_urls=media_urls,
            likes=likes,
            comments=comments,
            shares=shares,
            views=_to_int(_first_present(item, "videoViewCount", "views")),
            engagement_reliable=engagement_reliable,
        )

    def _map_and_finalize_posts(
        self, items: list[dict[str, Any]], max_posts: int
    ) -> list[ExtractedPost]:
        mapped: list[ExtractedPost] = []
        for item in items:
            try:
                post = self._map_post(item)
            except Exception:  # noqa: BLE001 - 1 ban ghi loi khong duoc lam hong ca lo
                logger.exception("apify_map_post_error")
                continue
            if post is not None:
                mapped.append(post)

        deduped = _dedupe_posts(mapped)
        sorted_posts = _sort_posts_newest_first(deduped)
        return sorted_posts[:max_posts]

    def _build_result(
        self,
        *,
        profile: ExtractedProfile | None,
        posts: list[ExtractedPost],
        effective_max: int,
        profile_error: str | None,
        posts_error: str | None,
    ) -> ExtractionResult:
        # Muc 10 - Partial data va chong bia du lieu: 4 truong hop A/B/C/D.
        if profile is None and not posts:
            reason = " | ".join(r for r in (profile_error, posts_error) if r) or (
                "Không lấy được dữ liệu Fanpage hoặc bài viết nào."
            )
            return ExtractionResult(status=ExtractionStatus.UNAVAILABLE, profile=None, posts=[], reason=reason)

        if profile is None and posts:
            return ExtractionResult(
                status=ExtractionStatus.PARTIAL,
                profile=None,
                posts=posts,
                reason=f"Không lấy được thông tin Fanpage: {profile_error or 'không rõ lý do'}.",
            )

        if profile is not None and not posts:
            return ExtractionResult(
                status=ExtractionStatus.PARTIAL,
                profile=profile,
                posts=[],
                reason=f"Không lấy được bài viết: {posts_error or 'không rõ lý do'}.",
            )

        if len(posts) < effective_max:
            return ExtractionResult(
                status=ExtractionStatus.PARTIAL,
                profile=profile,
                posts=posts,
                reason=f"Chỉ lấy được {len(posts)}/{effective_max} bài viết mong muốn.",
            )

        return ExtractionResult(status=ExtractionStatus.OK, profile=profile, posts=posts, reason=None)


# ---------------------------------------------------------------------------
# Helper thuan - khong goi mang, khong biet gi ve ApifyClient
# ---------------------------------------------------------------------------


def _first_present(item: dict[str, Any], *keys: str) -> Any:
    """Ho tro nhieu ten field tuong duong (Actor co the doi cau truc) -
    tra gia tri KHAC None/rong dau tien tim thay, None neu khong co key nao."""
    for key in keys:
        if key in item and item[key] not in (None, "", [], {}):
            return item[key]
    return None


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v]
    return [str(value)]


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        joined = " | ".join(str(v) for v in value if v)
        return joined or None
    text = str(value).strip()
    return text or None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(str(value).replace(",", "").replace(".", ""))
    except (ValueError, TypeError):
        return None


def _extract_reactions_total(item: dict[str, Any]) -> int | float | None:
    """"reactions" co the la so tong hoac 1 dict chi tiet theo loai cam xuc
    (vd {"like": 10, "love": 2}) - Unified Schema chi co 1 field "likes" nen
    cong don tat ca loai cam xuc lai neu la dict."""
    raw = _first_present(item, "likes", "likesCount", "reactionsCount", "reactions")
    if isinstance(raw, dict):
        total = 0
        found = False
        for v in raw.values():
            if isinstance(v, (int, float)):
                total += v
                found = True
        return total if found else None
    return raw


def _extract_media_urls(item: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    media = _first_present(item, "media", "attachments", "photos", "images")
    if isinstance(media, list):
        for m in media:
            if isinstance(m, str):
                urls.append(m)
            elif isinstance(m, dict):
                u = _first_present(m, "url", "image", "thumbnail", "photo_image", "src")
                if u:
                    urls.append(str(u))
    video_url = item.get("videoUrl") or item.get("video")
    if isinstance(video_url, str):
        urls.append(video_url)
    return [u for u in urls if isinstance(u, str) and u.startswith(("http://", "https://"))]


def _dedupe_posts(posts: list[ExtractedPost]) -> list[ExtractedPost]:
    """Loai ban ghi trung bang post ID hoac permalink (Muc 8 yeu cau #3)."""
    seen: set[str] = set()
    result: list[ExtractedPost] = []
    for post in posts:
        key = post.post_id or post.permalink
        if key in seen:
            continue
        seen.add(key)
        result.append(post)
    return result


def _sort_posts_newest_first(posts: list[ExtractedPost]) -> list[ExtractedPost]:
    """Sap xep theo thoi gian dang giam dan (moi nhat truoc). Parse
    published_at_text bang adapters.normalize (ho tro ca ISO 8601/Unix
    timestamp/chuoi tuong doi) de sap xep CHINH XAC theo thoi gian that -
    KHONG sap theo chuoi text tho (vd Unix timestamp dang so se sap SAI thu
    tu neu so chu so khac nhau nếu sắp như chuỗi). Bai KHONG co ngay (parse
    that bai) bi day xuong CUOI, khong lam sai thu tu cac bai co ngay hop le
    (Muc 8 yeu cau)."""
    from adapters.normalize import parse_relative_or_absolute_time

    def _key(post: ExtractedPost) -> tuple[int, float]:
        parsed = parse_relative_or_absolute_time(post.published_at_text)
        if parsed is None:
            return (0, 0.0)  # nhom "khong co ngay" - xep cuoi (nhom 0 < nhom 1)
        return (1, parsed.timestamp())

    return sorted(posts, key=_key, reverse=True)
