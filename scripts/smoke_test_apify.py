"""Smoke test THAT cho ApifyFacebookExtractor - goi Apify THAT (ton credit),
CHI chay thu cong tu dong lenh, KHONG bao gio chay trong unit test/CI (Muc 17
+ Muc 19: "Chay 1 smoke test that toi da 5 bai neu token local hoat dong").

Cach dung:
    python scripts/smoke_test_apify.py <facebook_page_url> [--max-posts N]

Vi du:
    python scripts/smoke_test_apify.py https://www.facebook.com/LinkPowerVN

Mac dinh CHI lay toi da 5 bai de tiet kiem credit Apify (--max-posts co the
tang len khi can, nhung KHONG bao gio vuot FACEBOOK_POST_LIMIT=30). Script
nay KHONG bao gio in gia tri APIFY_API_TOKEN ra terminal/log.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BASE_DIR / ".env")

from adapters import FacebookAdapter  # noqa: E402
from providers.facebook_apify_provider import (  # noqa: E402
    FACEBOOK_POST_LIMIT,
    ApifyFacebookExtractor,
)
from providers.facebook_extractor import ExtractionStatus  # noqa: E402


def _mask_token_status() -> str:
    token = os.getenv("APIFY_API_TOKEN", "")
    if not token:
        return "KHONG CO (chua khai bao trong .env)"
    return f"DA CO (do dai {len(token)} ky tu - khong hien thi gia tri)"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test ApifyFacebookExtractor")
    parser.add_argument("url", help="URL Fanpage Facebook can test")
    parser.add_argument(
        "--max-posts", type=int, default=5,
        help="So bai toi da lay ve (mac dinh 5 de tiet kiem credit, toi da 30)",
    )
    args = parser.parse_args()

    max_posts = min(args.max_posts, FACEBOOK_POST_LIMIT)

    print("=== Apify Facebook Provider - Smoke Test ===")
    print(f"URL: {args.url}")
    print(f"Max posts: {max_posts}")
    print(f"APIFY_API_TOKEN: {_mask_token_status()}")
    print()

    api_token = os.getenv("APIFY_API_TOKEN", "")
    if not api_token:
        print("LOI: Thieu APIFY_API_TOKEN trong .env - dung script tai day.")
        print("Xem APIFY_SETUP_AND_TEST.md de biet cach lay va khai bao token.")
        sys.exit(1)

    extractor = ApifyFacebookExtractor(
        api_token=api_token,
        pages_actor_id=os.getenv("APIFY_FACEBOOK_PAGES_ACTOR", "apify/facebook-pages-scraper"),
        posts_actor_id=os.getenv("APIFY_FACEBOOK_POSTS_ACTOR", "apify/facebook-posts-scraper"),
        max_posts=max_posts,
        timeout_seconds=int(os.getenv("APIFY_TIMEOUT_SECONDS", "180")),
    )

    print("Đang gọi Apify (Pages Scraper + Posts Scraper song song)...")
    result = await extractor.extract(args.url, max_posts)

    print()
    print(f"Trạng thái tổng thể: {result.status.value}")
    if result.reason:
        print(f"Lý do (nếu partial/unavailable): {result.reason}")

    print()
    if result.profile is not None:
        p = result.profile
        print("--- Page record (1) ---")
        print(f"  title: {p.display_name!r}")
        print(f"  categories: {p.categories!r}")
        print(f"  follower_count_text: {p.follower_count_text!r}")
        print(f"  likes_text (Page Likes, KHAC followers): {p.likes_text!r}")
        print(f"  rating_text: {p.rating_text!r}")
        print(f"  email: {p.email!r}")
        print(f"  phone: {p.phone!r}")
        print(f"  address: {p.address!r}")
        print(f"  website: {p.website!r}")
        print(f"  fields_missing: {p.fields_missing!r}")
    else:
        print("--- Page record: KHONG lay duoc (0 record) ---")

    print()
    print(f"--- Post records ({len(result.posts)}) ---")
    for i, post in enumerate(result.posts, start=1):
        print(
            f"  [{i}] id={post.post_id} date={post.published_at_text} "
            f"likes={post.likes} comments={post.comments} shares={post.shares} "
            f"type={post.type_hint}"
        )

    # Chay qua FacebookAdapter de xem ket qua SAU KHI normalize (Muc 17:
    # "Hien thi so bai sau normalize").
    adapter = FacebookAdapter(extractor=extractor, max_posts=max_posts)
    try:
        raw_profile = await adapter.resolve_profile(args.url)
        print()
        print(f"Sau normalize - display_name: {raw_profile.display_name!r}")
        print(f"Sau normalize - follower_count (da parse thanh int): {raw_profile.follower_count!r}")
    except Exception as exc:  # noqa: BLE001
        print(f"\nresolve_profile() qua FacebookAdapter that bai: {exc}")

    print()
    if result.status == ExtractionStatus.OK:
        print(f"KET QUA: Day du ({len(result.posts)}/{max_posts} bai).")
    elif result.status == ExtractionStatus.PARTIAL:
        print(f"KET QUA: Mot phan ({len(result.posts)}/{max_posts} bai, profile={'co' if result.profile else 'khong'}).")
    else:
        print("KET QUA: Khong du du lieu (data_unavailable).")


if __name__ == "__main__":
    asyncio.run(main())
