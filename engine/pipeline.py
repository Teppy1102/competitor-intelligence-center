"""run_facebook_analysis() - dieu phoi toan bo luong end-to-end theo dung
WORKFLOW.md (Sprint 1): Adapter (doi thu + LinkPower) -> Normalize ->
CompetitorDataset -> AnalysisEngine (AI) -> StatsBenchmarkEngine (lam giau
Benchmark bang so lieu code tinh) -> ReportGenerator -> luu job.

Quy tac MVP moi (Muc 5 - "co dinh 30 bai gan nhat", quyet dinh bo sung sau
Sprint Facebook Apify): KHONG con dung time_range de gioi han/loc bai viet -
`time_range_label_raw` duoc GIU trong signature CHI de tuong thich nguoc voi
client cu con gui field nay (deprecated, bi bo qua hoan toan, khong bao gio
lam that bai request - xem docstring run_facebook_analysis()). CompetitorDataset
(Unified Schema, DA KHOA) van yeu cau 1 TimeRange hop le nen ham nay van tao
1 gia tri MANG TINH MO TA (khong dung de loc) cho du field do.

Day la package MOI duy nhat de "noi day" cac package da lock kien truc cua
Sprint 2 (schemas/, analyzer/, benchmark/, report/) voi adapters/ +
providers/ - KHONG sua bat ky file nao trong cac package da lock, chi goi
qua public API cua chung.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from adapters import AdapterError, DataUnavailableError, FacebookAdapter
from adapters.facebook_adapter import FACEBOOK_POST_LIMIT
from adapters.normalize import (
    classify_post_type,
    compute_engagement_confidence,
    compute_profile_confidence,
    extract_hashtags,
)
from analyzer import AIClient, AnalysisEngine
from benchmark import BenchmarkDraft, StatsBenchmarkEngine, enforce_benchmark_rules
from providers.facebook_extractor import ExtractionStatus
from report import ReportGenerator, ReportMeta, render_report_html
from schemas import (
    Completeness,
    CompetitorDataset,
    ConfidenceLevel,
    EngagementMetrics,
    MIN_POSTS_FOR_BENCHMARK,
    NormalizedPost,
    NormalizedProfile,
    Platform,
    ProfileWithPosts,
    TimeRange,
    TimeRangeLabel,
)

from . import jobs as job_store

logger = logging.getLogger("cic.pipeline")

# TimeRange.label chi chap nhan 3 gia tri co dinh trong Unified Schema (da
# khoa - schemas/enums.py) - "3_months" duoc dung lam nhan MO TA co dinh cho
# CompetitorDataset.time_range du MVP khong con cho nguoi dung chon khoang
# thoi gian nua (Muc 5). Nhan nay KHONG anh huong den viec loc bai viet.
_NOMINAL_TIME_RANGE_LABEL = TimeRangeLabel.THREE_MONTHS
_NOMINAL_TIME_RANGE_DAYS = 90


class PipelineError(RuntimeError):
    """Loi khong the tiep tuc phan tich (vd khong lay duoc du lieu doi thu) -
    main.py bat loi nay va tra HTTP error co y nghia, KHONG phai 500 chung
    chung (WORKFLOW.md Sprint 1 muc 3)."""


@dataclass(frozen=True)
class PipelineResult:
    report_json: dict
    report_html: str
    job_id: str


async def run_facebook_analysis(
    *,
    competitor_url: str,
    reports_dir: Path,
    config: dict,
    adapter: FacebookAdapter,
    ai_client: AIClient,
    time_range_label_raw: str | None = None,
) -> PipelineResult:
    """`time_range_label_raw` la field DEPRECATED, CHI giu de tuong thich
    nguoc voi client cu con gui `time_range` trong request (Muc 5 + Muc 13):
    - KHONG duoc dung de loc/gioi han bai viet duoi bat ky hinh thuc nao.
    - KHONG bao gio lam that bai request du gia tri hop le hay khong.
    - Chi ghi log canh bao ky thuat (khong hien thi loi cho nguoi dung).
    """
    if time_range_label_raw:
        logger.warning(
            "deprecated_time_range_ignored value=%r - MVP hien tai luon phan tich "
            "%s bai gan nhat, khong con loc theo khoang thoi gian.",
            time_range_label_raw, FACEBOOK_POST_LIMIT,
        )

    job_id = job_store.new_job_id()
    logger.info("request_received job_id=%s competitor_url=%s", job_id, competitor_url)
    job_store.create_job(reports_dir, job_id, competitor_url, _NOMINAL_TIME_RANGE_LABEL.value)

    try:
        time_range = _build_nominal_time_range()

        logger.info("processing_start job_id=%s stage=data_collection", job_id)
        competitor_pwp, competitor_status = await _collect_profile_with_posts(
            adapter, competitor_url, time_range, required=True
        )

        linkpower_url = config["linkpower_profiles"]["facebook"]
        linkpower_pwp, _linkpower_status = await _collect_profile_with_posts(
            adapter, linkpower_url, time_range, required=False
        )

        completeness, data_gaps = _build_completeness(competitor_pwp, linkpower_pwp)

        dataset = CompetitorDataset(
            competitor=competitor_pwp,
            linkpower=linkpower_pwp,
            time_range=time_range,
            collected_at=datetime.now(timezone.utc),
            completeness=completeness,
        )

        logger.info("processing_done job_id=%s data_gaps=%s", job_id, data_gaps)

        logger.info("analysis_start job_id=%s stage=ai_analysis", job_id)
        analysis_engine = AnalysisEngine(
            ai_client=ai_client,
            max_posts_per_analysis=config.get("max_posts_per_analysis", 60),
        )
        raw_analysis = await analysis_engine.analyze(dataset)
        logger.info("analysis_done job_id=%s prompt_version=%s", job_id, raw_analysis.prompt_version)

        generated = ReportGenerator().generate(raw_analysis, job_id)

        benchmark_engine = StatsBenchmarkEngine()
        enriched_benchmark = benchmark_engine.compare(
            dataset, BenchmarkDraft(ai_drafted_section=generated.report.benchmark)
        )
        enriched_benchmark = enforce_benchmark_rules(enriched_benchmark, dataset)
        final_report = generated.report.model_copy(update={"benchmark": enriched_benchmark})

        final_html = render_report_html(
            final_report,
            dataset,
            ReportMeta(
                job_id=generated.job_id,
                prompt_version=generated.prompt_version,
                schema_version=generated.schema_version,
                generated_at=generated.generated_at,
            ),
        )

        report_json = final_report.model_dump(mode="json")
        report_json["job_id"] = job_id
        report_json["competitor_url"] = competitor_url
        report_json["completeness"] = completeness.model_dump(mode="json")
        report_json["generated_at"] = generated.generated_at.isoformat()
        # Muc 12 - frontend PHAI hien thi so bai THAT (khong phai 30 co dinh)
        # va trang thai du lieu ro rang (Day du/Mot phan/Khong du du lieu).
        report_json["posts_requested_limit"] = FACEBOOK_POST_LIMIT
        report_json["posts_analyzed"] = len(competitor_pwp.posts)
        report_json["data_status"] = _data_status_label(
            competitor_status, len(competitor_pwp.posts)
        )

        _persist_report(reports_dir, job_id, report_json, final_html)
        job_store.mark_completed(reports_dir, job_id)
        logger.info("request_completed job_id=%s", job_id)

        return PipelineResult(report_json=report_json, report_html=final_html, job_id=job_id)

    except DataUnavailableError as exc:
        logger.warning("request_failed job_id=%s reason=data_unavailable detail=%s", job_id, exc)
        job_store.mark_failed(reports_dir, job_id, str(exc))
        raise PipelineError(str(exc)) from exc
    except AdapterError as exc:
        logger.warning("request_failed job_id=%s reason=adapter_error detail=%s", job_id, exc)
        job_store.mark_failed(reports_dir, job_id, str(exc))
        raise PipelineError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("request_failed job_id=%s reason=unexpected", job_id)
        job_store.mark_failed(reports_dir, job_id, str(exc))
        raise PipelineError(f"Lỗi hệ thống khi phân tích: {exc}") from exc


def _build_nominal_time_range() -> TimeRange:
    """Gia tri MO TA (khong dung de loc) - xem docstring dau file. Luon la
    [hom nay - 90 ngay, hom nay] bat ke Fanpage thuc su co bai cu/moi the nao -
    CompetitorDataset.time_range (Unified Schema, da khoa) bat buoc phai co
    gia tri hop le nen khong the bo truong nay."""
    until = datetime.now(timezone.utc).date()
    since = until - timedelta(days=_NOMINAL_TIME_RANGE_DAYS)
    return TimeRange(label=_NOMINAL_TIME_RANGE_LABEL, since=since, until=until)


def _data_status_label(status: ExtractionStatus | None, posts_collected: int) -> str:
    """Muc 12 - 3 trang thai hien thi cho nguoi dung: "complete" (Day du),
    "partial" (Mot phan), "insufficient" (Khong du du lieu). Uu tien doc
    ExtractionStatus that (do FacebookAdapter luu lai tu provider) - chi
    fallback ve suy luan tu so bai neu khong co (vd adapter khac khong ho
    tro get_last_status())."""
    if posts_collected == 0:
        return "insufficient"
    if status == ExtractionStatus.OK:
        return "complete"
    if status == ExtractionStatus.PARTIAL:
        return "partial"
    # Fallback khi khong biet status that (khong nen xay ra voi FacebookAdapter
    # hien tai, nhung an toan hon la doan "complete" khi khong chac chan).
    return "complete" if posts_collected >= FACEBOOK_POST_LIMIT else "partial"


async def _collect_profile_with_posts(
    adapter: FacebookAdapter,
    url: str,
    time_range: TimeRange,
    *,
    required: bool,
) -> tuple[ProfileWithPosts, ExtractionStatus | None]:
    try:
        raw_profile = await adapter.resolve_profile(url)
        # since/until van duoc truyen de khop interface PlatformAdapter da
        # khoa (ARCHITECTURE.md muc 4) nhung FacebookAdapter.fetch_posts()
        # KHONG con dung 2 gia tri nay de loc (Muc 5) - xem adapters/facebook_adapter.py.
        raw_posts = await adapter.fetch_posts(
            url, time_range.since, time_range.until, FACEBOOK_POST_LIMIT
        )
    except DataUnavailableError:
        if required:
            raise
        # LinkPower (khong bat buoc) - "fail gracefully" theo ARCHITECTURE.md
        # muc 2.5: khong chan ca report, tra ve profile rong voi confidence
        # thap de Benchmark tu bien thanh "Khong du du lieu" (khong bia).
        return (
            ProfileWithPosts(
                profile=NormalizedProfile(
                    platform=Platform.FACEBOOK,
                    source_url=url,
                    display_name="LinkPower",
                    profile_data_confidence=ConfidenceLevel.LOW,
                ),
                posts=[],
            ),
            ExtractionStatus.UNAVAILABLE,
        )

    status = adapter.get_last_status(url)

    # raw_profile.follower_count va raw_post.published_at da duoc
    # FacebookAdapter parse san (tu follower_count_text/published_at_text) -
    # xem adapters/facebook_adapter.py. Pipeline chi ep kieu sang
    # Normalized*, khong parse lai.
    profile = NormalizedProfile(
        platform=Platform.FACEBOOK,
        source_url=url,
        display_name=raw_profile.display_name or "(Không rõ tên trang)",
        handle=raw_profile.handle,
        avatar_url=raw_profile.avatar_url,
        bio=raw_profile.bio,
        category=raw_profile.category,
        follower_count=raw_profile.follower_count,
        verified=raw_profile.verified,
        created_at=raw_profile.created_at,
        profile_data_confidence=compute_profile_confidence(raw_profile.fields_missing),
    )

    posts: list[NormalizedPost] = []
    for raw_post in raw_posts:
        published_at = raw_post.published_at
        if published_at is None:
            continue

        posts.append(
            NormalizedPost(
                post_id=raw_post.post_id,
                platform=Platform.FACEBOOK,
                published_at=published_at,
                type=classify_post_type(raw_post.post_type_hint, raw_post.permalink),
                caption_text=raw_post.caption_text or "",
                hashtags=extract_hashtags(raw_post.caption_text or ""),
                permalink=raw_post.permalink,
                thumbnail_url=raw_post.thumbnail_url,
                media_urls=raw_post.media_urls or [],
                engagement=EngagementMetrics(
                    likes=raw_post.likes,
                    comments=raw_post.comments,
                    shares=raw_post.shares,
                    views=raw_post.views,
                ),
                engagement_confidence=compute_engagement_confidence(
                    raw_post.likes, raw_post.comments, raw_post.engagement_reliable
                ),
            )
        )

    return ProfileWithPosts(profile=profile, posts=posts), status


def _build_completeness(
    competitor_pwp: ProfileWithPosts,
    linkpower_pwp: ProfileWithPosts,
) -> tuple[Completeness, list[str]]:
    """Muc 5 - khong con "expected theo time_range"; nguong toi thieu gio la
    1 hang so co dinh (dung chung MIN_POSTS_FOR_BENCHMARK cua schemas/thresholds.py,
    tranh dinh nghia lai 1 con so "toi thieu hop ly" khac o day)."""
    expected_min = MIN_POSTS_FOR_BENCHMARK

    data_gaps: list[str] = []
    if not linkpower_pwp.posts:
        data_gaps.append("Không lấy được dữ liệu bài viết LinkPower — Benchmark có thể bị hạn chế.")
    if len(competitor_pwp.posts) < expected_min:
        data_gaps.append(
            f"Chỉ thu thập được {len(competitor_pwp.posts)}/{FACEBOOK_POST_LIMIT} bài gần nhất "
            f"của đối thủ (cần tối thiểu {expected_min} bài để phân tích đầy đủ)."
        )
    elif len(competitor_pwp.posts) < FACEBOOK_POST_LIMIT:
        data_gaps.append(
            f"Chỉ thu thập được {len(competitor_pwp.posts)}/{FACEBOOK_POST_LIMIT} bài gần nhất "
            f"của đối thủ (Fanpage có thể có ít bài hơn hoặc nguồn dữ liệu bị giới hạn)."
        )
    if competitor_pwp.profile.follower_count is None:
        data_gaps.append("Không lấy được số lượng follower công khai của đối thủ.")

    completeness = Completeness(
        competitor_posts_collected=len(competitor_pwp.posts),
        competitor_posts_expected_min=expected_min,
        linkpower_posts_collected=len(linkpower_pwp.posts),
        linkpower_posts_expected_min=expected_min,
        data_gaps=data_gaps,
    )
    return completeness, data_gaps


def _persist_report(reports_dir: Path, job_id: str, report_json: dict, html: str) -> None:
    import json

    (reports_dir / f"{job_id}.json").write_text(
        json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (reports_dir / f"{job_id}.html").write_text(html, encoding="utf-8")
