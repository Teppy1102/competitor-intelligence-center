"""FacebookExtractor that su - dung Playwright (headless Chromium) de doc
du lieu CONG KHAI cua 1 Fanpage Facebook, dong vai tro "tu viet scraper" da
duoc LinkPower duyet (khong dung Apify/Phantombuster o MVP nay).

RANG BUOC BAT BUOC (theo yeu cau da duyet, khong duoc vi pham):
1. Khong dung tai khoan/mat khau/cookie/access token/phien dang nhap nao ca -
   moi request tao 1 BrowserContext HOAN TOAN moi (incognito that su, vi
   khong goi storage_state() khi tao context - xem _run_extraction()).
2. Chi doc du lieu DANG HIEN THI CONG KHAI - khong dien form dang nhap,
   khong bam nut nao tren trang, khong thu vuot CAPTCHA/checkpoint. Neu phat
   hien dang bi dua ve trang dang nhap/checkpoint, dung lai ngay va tra
   ExtractionStatus.UNAVAILABLE (xem _looks_like_login_wall()).
3. Khong luu cookie/localStorage/du lieu phien xuong dia hay bat ky noi nao -
   context.storage_state() KHONG duoc goi o bat ky dong nao trong file nay.
4. Moi request PHAI dong page, context, browser dung cach (try/finally) de
   giai phong RAM - kha ke ca khi co loi/exception.
5. Gioi han so bai viet o MAX_POSTS_HARD_CAP (20-30 bai gan nhat).
6. Gioi han so phien Playwright chay dong thoi (_SEMAPHORE) + timeout ro
   rang cho tung buoc (NAV_TIMEOUT_MS, OVERALL_TIMEOUT_SECONDS) de tranh qua
   tai server khi nhieu request cung luc.
7. Neu bi chan hoac du lieu khong du, tra status PARTIAL/UNAVAILABLE kem
   reason cu the - TUYET DOI khong bia so lieu thay the.

File nay CHI la Extractor (doc DOM tho) - khong biet gi ve
schemas.NormalizedProfile/NormalizedPost (xem facebook_extractor.py).
"""

from __future__ import annotations

import asyncio
import logging
import re

from .facebook_extractor import (
    ExtractedPost,
    ExtractedProfile,
    ExtractionResult,
    ExtractionStatus,
    FacebookExtractor,
)

logger = logging.getLogger("cic.facebook_playwright")

MAX_POSTS_HARD_CAP = 30  # yeu cau: gioi han MVP o 20-30 bai gan nhat
MAX_CONCURRENT_SESSIONS = 2  # gioi han so browser chay dong thoi tren server
NAV_TIMEOUT_MS = 20_000
OVERALL_TIMEOUT_SECONDS = 60

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_LOGIN_WALL_MARKERS = (
    "log in to facebook",
    "đăng nhập facebook",
    "you must log in",
    "checkpoint",
    "xác nhận đây là bạn",
    "security check",
)

_TIME_LINK_RE = re.compile(
    r"^\s*(\d+\s*(giây|phút|giờ|ngày|tuần|s|m|h|d|w)|hôm qua|yesterday|\d{1,2}\s*Tháng\s*\d{1,2}"
    r"|[A-Za-z]{3,9}\s+\d{1,2})\s*$",
    re.IGNORECASE,
)

_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SESSIONS)


class PlaywrightFacebookExtractor(FacebookExtractor):
    async def extract(self, url: str, max_posts: int) -> ExtractionResult:
        capped_max_posts = min(max_posts, MAX_POSTS_HARD_CAP)
        try:
            async with _semaphore:
                return await asyncio.wait_for(
                    self._run_extraction(url, capped_max_posts),
                    timeout=OVERALL_TIMEOUT_SECONDS,
                )
        except asyncio.TimeoutError:
            logger.warning("facebook_extract_timeout url=%s", url)
            return ExtractionResult(
                status=ExtractionStatus.UNAVAILABLE,
                profile=None,
                posts=[],
                reason="Hết thời gian chờ khi thu thập dữ liệu từ Facebook (quá tải hoặc phản hồi chậm).",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("facebook_extract_error url=%s", url)
            return ExtractionResult(
                status=ExtractionStatus.UNAVAILABLE,
                profile=None,
                posts=[],
                reason=f"Không thể truy cập Facebook: {exc}",
            )

    async def _run_extraction(self, url: str, max_posts: int) -> ExtractionResult:
        # Import cuc bo: chi doi hoi dependency playwright khi thuc su chay
        # extractor nay (khong bat buoc moi noi import providers/ phai co
        # sẵn playwright, vd tests dung FixtureFacebookExtractor).
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )
            # Context HOAN TOAN moi, khong storage_state -> an danh that su,
            # khong ke thua cookie/session tu bat ky lan chay nao truoc.
            context = await browser.new_context(
                user_agent=_USER_AGENT,
                viewport={"width": 1280, "height": 900},
                locale="vi-VN",
            )
            try:
                page = await context.new_page()
                page.set_default_timeout(NAV_TIMEOUT_MS)
                page.set_default_navigation_timeout(NAV_TIMEOUT_MS)

                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(1500)  # cho lazy content render

                body_text = await page.inner_text("body")
                if self._looks_like_login_wall(body_text, page.url):
                    return ExtractionResult(
                        status=ExtractionStatus.UNAVAILABLE,
                        profile=None,
                        posts=[],
                        reason=(
                            "Facebook yêu cầu đăng nhập/xác minh để xem trang này ở "
                            "chế độ ẩn danh — không thể thu thập dữ liệu công khai."
                        ),
                    )

                profile = await self._extract_profile(page, body_text)
                posts = await self._extract_posts(page, max_posts)

                if profile is None:
                    return ExtractionResult(
                        status=ExtractionStatus.UNAVAILABLE,
                        profile=None,
                        posts=[],
                        reason="Không đọc được thông tin Trang — có thể URL không phải Fanpage hợp lệ hoặc Trang không công khai.",
                    )

                status = ExtractionStatus.OK
                reason = None
                if not posts:
                    status = ExtractionStatus.PARTIAL
                    reason = "Không đọc được bài viết công khai nào trong nguồn dữ liệu hiện tại."
                elif len(posts) < max_posts:
                    status = ExtractionStatus.PARTIAL
                    reason = f"Chỉ đọc được {len(posts)}/{max_posts} bài viết mong muốn."

                return ExtractionResult(
                    status=status, profile=profile, posts=posts, reason=reason
                )
            finally:
                # Dong theo dung thu tu, KHONG goi storage_state() o bat ky
                # buoc nao - dam bao khong luu lai cookie/localStorage.
                await context.close()
                await browser.close()

    @staticmethod
    def _looks_like_login_wall(body_text: str, current_url: str) -> bool:
        lowered = (body_text or "").lower()
        if "checkpoint" in current_url or "/login" in current_url:
            return True
        return any(marker in lowered for marker in _LOGIN_WALL_MARKERS)

    async def _extract_profile(self, page, body_text: str) -> ExtractedProfile | None:
        fields_missing: list[str] = []

        display_name = None
        try:
            h1 = page.locator("h1").first
            if await h1.count() > 0:
                display_name = (await h1.inner_text()).strip() or None
        except Exception:  # noqa: BLE001
            pass
        if not display_name:
            fields_missing.append("display_name")
            return None  # khong co ten trang -> coi nhu khong doc duoc profile

        follower_count_text = None
        m = re.search(r"[\d.,]+\s*(?:K|Tr|M|B)?\s*(?:followers|người theo dõi)", body_text, re.IGNORECASE)
        if m:
            follower_count_text = m.group(0)
        else:
            fields_missing.append("follower_count")

        category = None
        m = re.search(r"Page\s*·\s*([^\n]+)|Trang\s*·\s*([^\n]+)", body_text)
        if m:
            category = (m.group(1) or m.group(2) or "").strip() or None
        else:
            fields_missing.append("category")

        avatar_url = None
        try:
            meta = page.locator('meta[property="og:image"]')
            if await meta.count() > 0:
                content = await meta.first.get_attribute("content")
                if content and content.startswith(("http://", "https://")):
                    avatar_url = content
        except Exception:  # noqa: BLE001
            pass
        if not avatar_url:
            fields_missing.append("avatar_url")

        bio = None
        try:
            meta_desc = page.locator('meta[property="og:description"]')
            if await meta_desc.count() > 0:
                bio = await meta_desc.first.get_attribute("content")
        except Exception:  # noqa: BLE001
            pass
        if not bio:
            fields_missing.append("bio")

        verified = "verified" in body_text.lower() or "đã xác minh" in body_text.lower()

        return ExtractedProfile(
            display_name=display_name,
            handle=None,
            avatar_url=avatar_url,
            bio=bio,
            category=category,
            follower_count_text=follower_count_text,
            verified=verified or None,
            fields_missing=fields_missing,
        )

    @staticmethod
    async def _scroll_until_enough_articles(page, articles, max_posts: int) -> int:
        """Facebook lazy-load bai viet khi cuon trang - can chu dong cuon
        (khong chi cho domcontentloaded) de co du bai cho max_posts (20-30
        theo yeu cau). Dung gioi han so lan cuon + dieu kien dung som khi so
        luong khong tang them (het bai hoac bi chan lazy-load tiep)."""
        max_scrolls = 8
        previous_count = await articles.count()
        for _ in range(max_scrolls):
            if previous_count >= max_posts:
                break
            await page.mouse.wheel(0, 2200)
            await page.wait_for_timeout(1200)
            current_count = await articles.count()
            if current_count <= previous_count:
                break  # khong tai them duoc nua - dung, tra ket qua hien co (PARTIAL)
            previous_count = current_count
        return previous_count

    async def _extract_posts(self, page, max_posts: int) -> list[ExtractedPost]:
        posts: list[ExtractedPost] = []
        try:
            articles = page.locator('[role="article"]')
            count = await self._scroll_until_enough_articles(page, articles, max_posts)
            count = min(count, max_posts * 2)  # bien du de loc bot
        except Exception:  # noqa: BLE001
            return posts

        for i in range(count):
            if len(posts) >= max_posts:
                break
            try:
                article = articles.nth(i)
                extracted = await self._extract_one_post(article)
                if extracted is not None:
                    posts.append(extracted)
            except Exception:  # noqa: BLE001
                continue  # 1 bai loi khong duoc lam sap ca lan thu thap

        return posts

    async def _extract_one_post(self, article) -> ExtractedPost | None:
        links = article.locator("a[href]")
        link_count = await links.count()

        permalink = None
        published_at_text = None
        for j in range(link_count):
            link = links.nth(j)
            text = (await link.inner_text() or "").strip()
            if text and _TIME_LINK_RE.match(text):
                href = await link.get_attribute("href")
                if href:
                    permalink = href
                    published_at_text = text
                    break

        if not permalink:
            return None  # khong tim duoc link thoi gian -> khong chac day la 1 bai dang hop le

        post_id_match = re.search(r"/(\d{6,})", permalink)
        post_id = post_id_match.group(1) if post_id_match else permalink

        type_hint = "text"
        if "/reel" in permalink:
            type_hint = "reel"
        elif "/videos/" in permalink:
            type_hint = "video"
        elif "/photos/" in permalink or "/photo.php" in permalink or "/photo/" in permalink:
            type_hint = "photo"

        full_text = (await article.inner_text() or "").strip()
        caption_text = self._strip_boilerplate(full_text)

        thumbnail_url = None
        try:
            imgs = article.locator("img")
            img_count = min(await imgs.count(), 5)
            for k in range(img_count):
                src = await imgs.nth(k).get_attribute("src")
                # Facebook dung "data:image/svg+xml,..." lam placeholder khi
                # anh that chua tai xong - khong phai URL that, bo qua (va
                # NormalizedPost.thumbnail_url la HttpUrl, khong chap nhan
                # scheme "data:").
                if src and src.startswith(("http://", "https://")):
                    thumbnail_url = src
                    break
        except Exception:  # noqa: BLE001
            pass

        likes, comments, shares, engagement_reliable = self._extract_engagement(full_text)

        return ExtractedPost(
            post_id=post_id,
            permalink=permalink if permalink.startswith("http") else f"https://www.facebook.com{permalink}",
            caption_text=caption_text,
            published_at_text=published_at_text,
            type_hint=type_hint,
            thumbnail_url=thumbnail_url,
            media_urls=[thumbnail_url] if thumbnail_url else [],
            likes=likes,
            comments=comments,
            shares=shares,
            views=None,
            engagement_reliable=engagement_reliable,
        )

    @staticmethod
    def _strip_boilerplate(text: str) -> str:
        boilerplate_lines = {
            "like", "comment", "share", "thích", "bình luận", "chia sẻ",
            "all reactions:", "most relevant",
        }
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        kept = [ln for ln in lines if ln.lower() not in boilerplate_lines]
        # Bo dong dau (thuong la ten tac gia) va dong thoi gian tuong doi -
        # phan con lai la caption gan dung nhat co the lay duoc best-effort.
        return " ".join(kept[2:]) if len(kept) > 2 else " ".join(kept)

    @staticmethod
    def _extract_engagement(text: str) -> tuple[int | None, int | None, int | None, bool]:
        likes = comments = shares = None
        reliable = False

        m = re.search(r"([\d.,]+)\s*(?:bình luận|comments?)\b", text, re.IGNORECASE)
        if m:
            comments = _parse_int(m.group(1))
            reliable = True

        m = re.search(r"([\d.,]+)\s*(?:lượt chia sẻ|shares?)\b", text, re.IGNORECASE)
        if m:
            shares = _parse_int(m.group(1))
            reliable = True

        m = re.search(r"([\d.,]+)\s*(?:người khác|others|reactions?)\b", text, re.IGNORECASE)
        if m:
            likes = _parse_int(m.group(1))
            reliable = True

        return likes, comments, shares, reliable


def _parse_int(text: str) -> int | None:
    cleaned = text.replace(",", "").replace(".", "")
    try:
        return int(cleaned)
    except ValueError:
        return None
