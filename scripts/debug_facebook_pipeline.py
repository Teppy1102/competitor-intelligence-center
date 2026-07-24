"""Debug script CUC BO - audit toan bo pipeline tu raw Apify response den
final report, dump tung buoc ra debug/*.json de kiem tra field coverage that.

CHI dung local, KHONG bao gio chay trong CI/production. KHONG hien thi API
token. Cac file debug/*.json chua du lieu Facebook that -> da gitignore
(xem .gitignore: "debug/*.json").

Cach dung:
    python scripts/debug_facebook_pipeline.py <facebook_page_url> [--max-posts N] [--skip-ai]

Vi du:
    python scripts/debug_facebook_pipeline.py https://www.facebook.com/LinkPowerVN --max-posts 30

--skip-ai: bo qua goi OpenAI that (chi audit den analysis_input.json) - dung
khi chi can kiem tra coverage raw/normalize, khong can ton chi phi AI.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BASE_DIR / ".env")

from adapters.facebook_adapter import FACEBOOK_POST_LIMIT  # noqa: E402
from adapters.normalize import (  # noqa: E402
    classify_post_type,
    compute_engagement_confidence,
    compute_profile_confidence,
    extract_hashtags,
)
from analyzer import AnalysisEngine  # noqa: E402
from providers.ai_provider import get_ai_client  # noqa: E402
from providers.facebook_apify_provider import ApifyFacebookExtractor  # noqa: E402
from report import ReportGenerator  # noqa: E402
from schemas import (  # noqa: E402
    CompetitorDataset,
    Completeness,
    ConfidenceLevel,
    EngagementMetrics,
    NormalizedPost,
    NormalizedProfile,
    Platform,
    ProfileWithPosts,
    TimeRange,
    TimeRangeLabel,
)

DEBUG_DIR = BASE_DIR / "debug"
DEBUG_DIR.mkdir(exist_ok=True)


def _dump(name: str, data: Any) -> None:
    path = DEBUG_DIR / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"  -> {path.relative_to(BASE_DIR)} ({len(json.dumps(data, default=str))} bytes)")


def _mask_token_status() -> str:
    token = os.getenv("APIFY_API_TOKEN", "")
    return f"DA CO (do dai {len(token)} ky tu)" if token else "KHONG CO"


def _coverage_report(raw_posts: list[dict]) -> None:
    """PHAN 1 - bang coverage field tho, KHONG ket luan thieu du lieu truoc
    khi in bang nay (yeu cau: 'Khong ket luan thieu du lieu truoc khi kiem
    tra coverage that')."""
    fields_to_check = {
        "text": ("text", "postText", "message", "caption", "description"),
        "url": ("url", "postUrl", "facebookUrl", "permalink", "link", "topLevelUrl"),
        "date": ("time", "timestamp", "date", "publishedAt", "published_at", "postDate", "createdTime"),
        "likes": ("likes", "numberOfLikes", "likesCount", "reactionsCount", "reactions"),
        "comments": ("comments", "numberOfComments", "commentsCount"),
        "shares": ("shares", "numberOfShares", "sharesCount"),
        "media": ("media", "images", "attachments", "video", "videoUrl"),
        "media_type": ("isVideo", "media_type", "mediaType"),
    }

    total = len(raw_posts)
    print(f"\n=== FIELD COVERAGE ({total} bai tho tu Apify) ===")
    print(f"{'Field':<12} {'So bai co du lieu':<20} {'Ty le':<8}")
    for label, candidates in fields_to_check.items():
        count = sum(
            1 for p in raw_posts
            if any(p.get(k) not in (None, "", [], {}) for k in candidates)
        )
        pct = round(count / total * 100, 1) if total else 0.0
        print(f"{label:<12} {count}/{total:<17} {pct}%")

    print("\n=== KEY THUC TE XUAT HIEN TRONG DATASET (dung de doi chieu candidate list) ===")
    all_keys: set[str] = set()
    for p in raw_posts:
        all_keys.update(p.keys())
    print(sorted(all_keys))


async def main() -> None:
    parser = argparse.ArgumentParser(description="Debug toan bo Facebook analysis pipeline")
    parser.add_argument("url", help="URL Fanpage Facebook can audit")
    parser.add_argument("--max-posts", type=int, default=FACEBOOK_POST_LIMIT)
    parser.add_argument("--skip-ai", action="store_true", help="Bo qua goi OpenAI that")
    parser.add_argument(
        "--reuse", action="store_true",
        help="Tai su dung debug/raw_page.json + debug/raw_posts.json da co (khong goi lai Apify, tiet kiem credit)",
    )
    args = parser.parse_args()
    max_posts = min(args.max_posts, FACEBOOK_POST_LIMIT)

    print("=== Debug Facebook Pipeline ===")
    print(f"URL: {args.url}")
    print(f"Max posts: {max_posts}")
    print(f"APIFY_API_TOKEN: {_mask_token_status()}")

    api_token = os.getenv("APIFY_API_TOKEN", "")
    if not api_token:
        print("LOI: Thieu APIFY_API_TOKEN trong .env")
        sys.exit(1)

    extractor = ApifyFacebookExtractor(
        api_token=api_token,
        pages_actor_id=os.getenv("APIFY_FACEBOOK_PAGES_ACTOR", "apify/facebook-pages-scraper"),
        posts_actor_id=os.getenv("APIFY_FACEBOOK_POSTS_ACTOR", "apify/facebook-posts-scraper"),
        max_posts=max_posts,
        timeout_seconds=int(os.getenv("APIFY_TIMEOUT_SECONDS", "180")),
    )

    # --- Buoc 1: RAW Apify response (truoc khi mapping) ---
    raw_page_path = DEBUG_DIR / "raw_page.json"
    raw_posts_path = DEBUG_DIR / "raw_posts.json"

    if args.reuse and raw_page_path.exists() and raw_posts_path.exists():
        print(f"\n--reuse: doc lai {raw_page_path.name}/{raw_posts_path.name} da co, khong goi lai Apify.")
        page_items = json.loads(raw_page_path.read_text(encoding="utf-8"))
        post_items = json.loads(raw_posts_path.read_text(encoding="utf-8"))
    else:
        print("\nDang goi Apify (Pages + Posts)...")
        pages_outcome, posts_outcome = await asyncio.gather(
            extractor._run_pages_actor(args.url),
            extractor._run_posts_actor(args.url, max_posts),
        )
        if pages_outcome.error:
            print(f"  [Pages] loi: {pages_outcome.error}")
        if posts_outcome.error:
            print(f"  [Posts] loi: {posts_outcome.error}")
        page_items = pages_outcome.items
        post_items = posts_outcome.items
        print("\n=== BUOC 1: RAW APIFY RESPONSE ===")
        _dump("raw_page.json", page_items)
        _dump("raw_posts.json", post_items)

    _coverage_report(post_items)

    # --- Buoc 2: Extracted (mapped tu raw, truoc normalize) ---
    profile = extractor._map_profile(page_items) if page_items else None
    extracted_posts = extractor._map_and_finalize_posts(post_items, max_posts)

    # --- Buoc 3: Normalized (Unified Schema that) ---
    print("\n=== BUOC 2+3: NORMALIZE (Unified Schema) ===")
    if profile is None:
        print("  KHONG co Page record - dung tai day.")
        sys.exit(1)

    normalized_profile = NormalizedProfile(
        platform=Platform.FACEBOOK,
        source_url=args.url,
        display_name=profile.display_name or "(Không rõ tên trang)",
        handle=profile.handle,
        avatar_url=profile.avatar_url,
        bio=profile.bio,
        category=profile.category,
        follower_count=_parse_follower(profile.follower_count_text),
        verified=profile.verified,
        profile_data_confidence=compute_profile_confidence(profile.fields_missing),
    )
    _dump("normalized_profile.json", json.loads(normalized_profile.model_dump_json()))

    normalized_posts: list[NormalizedPost] = []
    for ep in extracted_posts:
        from adapters.normalize import parse_relative_or_absolute_time

        published_at = parse_relative_or_absolute_time(ep.published_at_text)
        if published_at is None:
            continue
        normalized_posts.append(
            NormalizedPost(
                post_id=ep.post_id,
                platform=Platform.FACEBOOK,
                published_at=published_at,
                type=classify_post_type(ep.type_hint, ep.permalink),
                caption_text=ep.caption_text or "",
                hashtags=extract_hashtags(ep.caption_text or ""),
                permalink=ep.permalink,
                thumbnail_url=ep.thumbnail_url,
                media_urls=ep.media_urls or [],
                engagement=EngagementMetrics(
                    likes=ep.likes, comments=ep.comments, shares=ep.shares, views=ep.views
                ),
                engagement_confidence=compute_engagement_confidence(
                    ep.likes, ep.comments, ep.engagement_reliable
                ),
            )
        )
    _dump("normalized_posts.json", [json.loads(p.model_dump_json()) for p in normalized_posts])

    posts_with_text = sum(1 for p in normalized_posts if (p.caption_text or "").strip())
    print(f"  Bai sau normalize: {len(normalized_posts)} (co text: {posts_with_text})")

    # --- Buoc 4: CompetitorDataset (dung LinkPower gia lap don gian - chi de audit competitor) ---
    until = datetime.now(timezone.utc).date()
    since = until - timedelta(days=90)
    dataset = CompetitorDataset(
        competitor=ProfileWithPosts(profile=normalized_profile, posts=normalized_posts),
        linkpower=ProfileWithPosts(
            profile=NormalizedProfile(
                platform=Platform.FACEBOOK,
                source_url="https://www.facebook.com/LinkPowerVN",
                display_name="LinkPower (debug placeholder)",
                profile_data_confidence=ConfidenceLevel.LOW,
            ),
            posts=[],
        ),
        time_range=TimeRange(label=TimeRangeLabel.THREE_MONTHS, since=since, until=until),
        collected_at=datetime.now(timezone.utc),
        completeness=Completeness(
            competitor_posts_collected=len(normalized_posts),
            competitor_posts_expected_min=5,
            linkpower_posts_collected=0,
            linkpower_posts_expected_min=5,
            data_gaps=[],
        ),
    )

    if args.skip_ai:
        print("\n--skip-ai: dung tai day (khong goi OpenAI that).")
        _dump("analysis_input.json", json.loads(dataset.model_dump_json()))
        return

    # --- Buoc 5: Analysis Engine (goi AI that) ---
    print("\n=== BUOC 5: ANALYSIS ENGINE (goi OpenAI that) ===")
    ai_client = get_ai_client()
    analysis_engine = AnalysisEngine(ai_client=ai_client)
    from analyzer.prompt_builder import compute_dataset_stats

    stats = compute_dataset_stats(dataset)
    _dump(
        "analysis_input.json",
        {
            "dataset": json.loads(dataset.model_dump_json()),
            "eligibility": stats.eligibility.__dict__,
            "benchmark_eligible": stats.benchmark_eligible,
        },
    )

    raw_analysis = await analysis_engine.analyze(dataset)
    _dump("analysis_output.json", {"raw_html": raw_analysis.raw_html, "prompt_version": raw_analysis.prompt_version})

    # --- Buoc 6: Report Generator ---
    print("\n=== BUOC 6: REPORT GENERATOR ===")
    generated = ReportGenerator().generate(raw_analysis, job_id="debug")
    _dump("final_report.json", json.loads(generated.report.model_dump_json()))

    print("\n=== TOM TAT SECTION CO DU LIEU ===")
    report = generated.report
    print(f"  ai_summary rong?            {report.executive_summary.ai_summary in ('', 'Không đủ dữ liệu')}")
    print(f"  content_pillars so luong:   {len(report.content_analysis.content_pillars)}")
    print(f"  content_type_breakdown:     {len(report.content_analysis.content_type_breakdown)}")
    print(f"  hook_patterns:              {len(report.content_style.hook_patterns)}")
    print(f"  cta_patterns:               {len(report.content_style.cta_patterns)}")
    print(f"  top_performing_posts:       {len(report.engagement_analysis.top_performing_posts)}")


def _parse_follower(text: str | None):
    from adapters.normalize import parse_follower_count

    return parse_follower_count(text)


if __name__ == "__main__":
    asyncio.run(main())
