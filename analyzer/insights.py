"""analyzer/insights.py - phan tich dinh luong/rule-based tinh THUAN BANG
CODE, KHONG phu thuoc AI (bo sung sau audit "report dinh tinh trong du da co
30 bai that" - xem PHAN 4/5/6 cua yeu cau audit).

Nguyen tac: moi ham o day CHI doc schemas.NormalizedPost/EngagementMetrics -
khong goi AI, khong I/O. Duoc report/rules.py goi SAU KHI parse HTML AI, de
GHI DE cac truong co the tinh chinh xac bang code (top posts, content type
breakdown, hook/CTA pattern, content pillar count/percentage that) - dung
tinh than da chung minh voi publishing_pattern (report/rules.py da lam tu
Sprint 2, o day mo rong cho cac truong con lai dang phu thuoc 100% vao AI).

Ly do can module nay (audit thuc te - xem debug/analysis_output.json):
AI khong tuan thu dung ten data-field cho nhieu section (vd viet "pillar_name"
thay vi "pillar", khong dien post_count/percentage) khien parser tra ve
mac dinh 0/rong - KHONG PHAI vi thieu du lieu that. Cac ham o day tinh truc
tiep tu NormalizedPost that, khong phu thuoc AI co tuan thu dung markup hay
khong.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass

from schemas import (
    ContentPillar,
    ContentTypeBreakdownEntry,
    EngagementPostRef,
    NormalizedPost,
)

NO_DATA = "Không đủ dữ liệu"

MIN_POSTS_WITH_TEXT_FOR_CONTENT = 5
"""Trung voi schemas.thresholds.MIN_POSTS_FOR_CONTENT_SECTIONS - khai bao
rieng o day (khong import cheo dinh menh) vi day la nguong cho DU LIEU TEXT
THAT (Phan 3 yeu cau: 'content_tone_style' phai dua tren so bai CO TEXT,
khong phai chi so bai thu thap duoc)."""


# ---------------------------------------------------------------------------
# PHAN 4.1 - Top bai theo engagement (code tinh, KHONG can AI)
# ---------------------------------------------------------------------------


def engagement_score(post: NormalizedPost) -> float:
    """engagement_score = likes + 2*comments + 3*shares (Phan 4.1 - co dinh,
    co test rieng). Field None duoc coi la 0 CHI trong phep cong diem xep
    hang (khong anh huong den engagement_confidence/averages o cho khac)."""
    e = post.engagement
    return (e.likes or 0) + 2 * (e.comments or 0) + 3 * (e.shares or 0)


def _has_any_engagement_signal(post: NormalizedPost) -> bool:
    e = post.engagement
    return e.likes is not None or e.comments is not None or e.shares is not None


def rank_posts_by_engagement(posts: list[NormalizedPost]) -> list[NormalizedPost]:
    """Chi xep hang bai CO it nhat 1 chi so tuong tac cong khai (khong bia
    bai khong co so lieu nao ca) - sap giam dan theo engagement_score."""
    ranked = [p for p in posts if _has_any_engagement_signal(p)]
    return sorted(ranked, key=engagement_score, reverse=True)


def _excerpt(caption_text: str, length: int = 120) -> str:
    text = (caption_text or "").strip().replace("\n", " ")
    if not text:
        return "(không có nội dung caption)"
    return text[:length] + ("…" if len(text) > length else "")


def build_top_performing_refs(
    posts: list[NormalizedPost], limit: int = 5
) -> list[EngagementPostRef]:
    """Phan 4.1 - Top 5 KHONG yeu cau AI, tra post URL + excerpt + ly do dua
    tren so lieu that. Neu du lieu engagement chi la 1 phan (vd thieu shares
    o 1 so bai), van xep hang duoc tren nhung gi co - ghi chu ro trong reason."""
    ranked = rank_posts_by_engagement(posts)[:limit]
    refs: list[EngagementPostRef] = []
    for post in ranked:
        e = post.engagement
        score = engagement_score(post)
        reason = (
            f"“{_excerpt(post.caption_text)}” — điểm tương tác {score:.0f} "
            f"(likes={e.likes if e.likes is not None else NO_DATA}, "
            f"comments={e.comments if e.comments is not None else NO_DATA}, "
            f"shares={e.shares if e.shares is not None else NO_DATA}); "
            f"xếp hạng trên dữ liệu tương tác công khai hiện có."
        )
        summary = (
            f"{e.likes if e.likes is not None else 0} likes · "
            f"{e.comments if e.comments is not None else 0} bình luận · "
            f"{e.shares if e.shares is not None else 0} lượt chia sẻ"
        )
        refs.append(
            EngagementPostRef(permalink=post.permalink, reason=reason, engagement_summary=summary)
        )
    return refs


def build_underperforming_refs(
    posts: list[NormalizedPost], limit: int = 3
) -> list[EngagementPostRef]:
    ranked = rank_posts_by_engagement(posts)
    if len(ranked) <= limit:
        return []  # qua it bai co du lieu de noi "yeu hon" co y nghia
    bottom = list(reversed(ranked))[:limit]
    refs: list[EngagementPostRef] = []
    for post in bottom:
        score = engagement_score(post)
        reason = (
            f"“{_excerpt(post.caption_text)}” — điểm tương tác {score:.0f}, "
            f"thấp hơn phần lớn bài khác trong tập dữ liệu đã thu thập."
        )
        refs.append(EngagementPostRef(permalink=post.permalink, reason=reason))
    return refs


# ---------------------------------------------------------------------------
# PHAN 4.4 - Engagement averages (KHONG dung 0 thay null, giu None thuc su)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EngagementAverages:
    avg_likes: float | None
    avg_comments: float | None
    avg_shares: float | None
    avg_total_engagement: float | None
    sample_size: int


def compute_engagement_averages(posts: list[NormalizedPost]) -> EngagementAverages:
    """Chi tinh tren bai CO gia tri that (khong None) cho tung chi so rieng
    biet - 1 bai thieu "shares" khong lam mat di gia tri "likes" cua no
    trong trung binh likes (Phan 4.4: khong dung 0 thay cho null, nhung neu
    Actor tra 0 ro rang thi giu 0)."""
    likes = [p.engagement.likes for p in posts if p.engagement.likes is not None]
    comments = [p.engagement.comments for p in posts if p.engagement.comments is not None]
    shares = [p.engagement.shares for p in posts if p.engagement.shares is not None]
    totals = [
        engagement_score(p) for p in posts if _has_any_engagement_signal(p)
    ]

    def _avg(values: list[float]) -> float | None:
        return round(statistics.mean(values), 1) if values else None

    return EngagementAverages(
        avg_likes=_avg(likes),
        avg_comments=_avg(comments),
        avg_shares=_avg(shares),
        avg_total_engagement=_avg(totals),
        sample_size=len(totals),
    )


# ---------------------------------------------------------------------------
# PHAN 4.2 - Phan bo loai noi dung (wire lai compute_content_type_breakdown
# da co san trong analyzer/stats.py - truoc day tinh ra nhung KHONG duoc dua
# vao report cuoi cung, day chinh la 1 nguyen nhan "0%" duoc audit thay).
# ---------------------------------------------------------------------------


def build_content_type_breakdown(posts: list[NormalizedPost]) -> list[ContentTypeBreakdownEntry]:
    from .stats import compute_content_type_breakdown

    return compute_content_type_breakdown(posts)


# ---------------------------------------------------------------------------
# PHAN 5 - Content Pillar: AI de xuat nhan + example_post_permalinks, CODE
# doi chieu lai voi bai that, loai nhan khong map duoc, tu tinh post_count/
# percentage THAT (khong tin so AI tu bao cao).
# ---------------------------------------------------------------------------


def recompute_content_pillars(
    ai_pillars: list[ContentPillar], posts: list[NormalizedPost]
) -> list[ContentPillar]:
    """Phan 5 - quy tac bat buoc:
    1. Moi bai co text duoc gan vao DUY NHAT 1 pillar (uu tien thu tu AI de
       xuat) hoac "Khac" neu khong pillar nao claim.
    2. post_count/percentage tinh TU danh sach bai da gan (khong dung so AI
       tu bao cao).
    3. Pillar khong co bai nao map duoc (0 sau khi doi chieu) bi LOAI HOAN
       TOAN - khong xuat hien trong ket qua (khong duoc de count=0)."""
    posts_with_text = [p for p in posts if (p.caption_text or "").strip()]
    if not posts_with_text:
        return []

    permalink_to_post = {str(p.permalink): p for p in posts_with_text}
    claimed: set[str] = set()
    pillar_assignments: list[tuple[str, list[NormalizedPost]]] = []

    for pillar in ai_pillars:
        label = (pillar.pillar or "").strip()
        if not label:
            continue
        matched: list[NormalizedPost] = []
        for permalink in pillar.example_post_permalinks:
            key = str(permalink)
            if key in permalink_to_post and key not in claimed:
                matched.append(permalink_to_post[key])
                claimed.add(key)
        if matched:  # bo qua hoan toan nhan khong map duoc bai nao (yeu cau #5)
            pillar_assignments.append((label, matched))

    leftover = [p for p in posts_with_text if str(p.permalink) not in claimed]
    if leftover:
        pillar_assignments.append(("Khác", leftover))

    total_classified = len(posts_with_text)
    result: list[ContentPillar] = []
    for label, matched_posts in pillar_assignments:
        count = len(matched_posts)
        percentage = round(count / total_classified * 100, 1) if total_classified else 0.0
        result.append(
            ContentPillar(
                pillar=label,
                post_count=count,
                percentage=percentage,
                example_post_permalinks=[p.permalink for p in matched_posts[:5]],
            )
        )

    result.sort(key=lambda p: p.post_count, reverse=True)
    return result


# ---------------------------------------------------------------------------
# PHAN 6 - Hook detection (regex/tu khoa, khong phu thuoc AI/nganh cu the)
# ---------------------------------------------------------------------------

_HOOK_RULES: list[tuple[str, re.Pattern]] = [
    ("Đặt câu hỏi mở đầu", re.compile(r"^[^.!\n]{0,80}\?", re.MULTILINE)),
    ("Dùng số liệu/con số cụ thể", re.compile(r"^\s*\d+[\s.,]|(?:top|list)\s*\d+", re.IGNORECASE)),
    ("Cảnh báo/nguy cơ", re.compile(r"\b(cảnh báo|nguy cơ|rủi ro|coi chừng|sai lầm)\b", re.IGNORECASE)),
    ("Nêu vấn đề/nỗi đau", re.compile(r"\b(vấn đề|nỗi đau|thất bại|khó khăn|áp lực|ám ảnh)\b", re.IGNORECASE)),
    ("Nhấn mạnh lợi ích", re.compile(r"\b(lợi ích|giải pháp|bí quyết|hiệu quả|tăng trưởng)\b", re.IGNORECASE)),
    ("Case study/câu chuyện thực tế", re.compile(r"\b(case study|câu chuyện|khách hàng|chia sẻ từ)\b", re.IGNORECASE)),
    ("Trích dẫn", re.compile(r"^[\"“]")),
    ("Thông báo sự kiện", re.compile(r"\b(hội thảo|sự kiện|webinar|khai giảng|đăng ký ngay)\b", re.IGNORECASE)),
    ("Nội dung giáo dục/kiến thức", re.compile(r"\b(kiến thức|hướng dẫn|cách để|bạn có biết)\b", re.IGNORECASE)),
]

_HOOK_WINDOW = 250


def classify_hook(caption_text: str) -> str | None:
    """Phan tich {_HOOK_WINDOW} ky tu dau caption - tra ve NHAN dau tien
    khop, None neu khong nhan dang duoc mau nao (se roi vao "Khac")."""
    text = (caption_text or "").strip()[: _HOOK_WINDOW]
    if not text:
        return None
    for label, pattern in _HOOK_RULES:
        if pattern.search(text):
            return label
    return None


def detect_hook_patterns(posts: list[NormalizedPost]) -> list[str]:
    """Phan 6 - tra danh sach chuoi mo ta (kem so lieu that, vi
    ContentStyleSection.hook_patterns la list[str] co dinh trong Unified
    Schema - khong doi duoc kieu du lieu nen nhet so lieu vao chuoi hien
    thi). KHONG bao gio tra rong neu co bai co text - toi thieu tra 1 dong
    "Khong nhan dang duoc mau hook ro rang"."""
    texted_posts = [p for p in posts if (p.caption_text or "").strip()]
    if not texted_posts:
        return []

    counts: dict[str, int] = {}
    examples: dict[str, str] = {}
    unclassified = 0
    for post in texted_posts:
        label = classify_hook(post.caption_text)
        if label is None:
            unclassified += 1
            continue
        counts[label] = counts.get(label, 0) + 1
        examples.setdefault(label, _excerpt(post.caption_text, 80))

    total = len(texted_posts)
    lines = [
        f"{label} ({count}/{total} bài, {round(count / total * 100)}%) — vd: “{examples[label]}”"
        for label, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]
    if unclassified:
        pct = round(unclassified / total * 100)
        lines.append(f"Không nhận dạng được mẫu hook rõ ràng ({unclassified}/{total} bài, {pct}%)")
    return lines


# ---------------------------------------------------------------------------
# PHAN 6 - CTA detection
# ---------------------------------------------------------------------------

_CTA_RULES: list[tuple[str, re.Pattern]] = [
    ("Đăng ký", re.compile(r"\b(đăng ký|đăng kí)\b", re.IGNORECASE)),
    ("Tìm hiểu thêm", re.compile(r"\b(tìm hiểu thêm|xem thêm)\b", re.IGNORECASE)),
    ("Xem chi tiết", re.compile(r"\b(xem chi tiết|chi tiết tại)\b", re.IGNORECASE)),
    ("Inbox", re.compile(r"\b(inbox|nhắn tin)\b", re.IGNORECASE)),
    ("Liên hệ", re.compile(r"\b(liên hệ|hotline|gọi ngay)\b", re.IGNORECASE)),
    ("Kêu gọi bình luận", re.compile(r"\b(bình luận|comment)\b", re.IGNORECASE)),
    ("Kêu gọi chia sẻ", re.compile(r"\b(chia sẻ ngay|share bài)\b", re.IGNORECASE)),
    ("Tham gia", re.compile(r"\b(tham gia|ghi danh)\b", re.IGNORECASE)),
    ("Đọc thêm", re.compile(r"\b(đọc thêm|đọc tiếp)\b", re.IGNORECASE)),
    ("Truy cập website", re.compile(r"\b(truy cập|website|link:|http)\b", re.IGNORECASE)),
]


def classify_cta(caption_text: str) -> str | None:
    text = caption_text or ""
    for label, pattern in _CTA_RULES:
        if pattern.search(text):
            return label
    return None


def detect_cta_patterns(posts: list[NormalizedPost]) -> list[str]:
    """Phan 6 - neu KHONG tim thay CTA ro rang, PHAI tra goc nhin cu the
    ('Phan lon bai viet khong su dung CTA truc tiep'/...) - KHONG duoc tra
    'Khong du du lieu' mien la code THAT SU dem duoc so bai (yeu cau ro rang
    cua Phan 6)."""
    texted_posts = [p for p in posts if (p.caption_text or "").strip()]
    if not texted_posts:
        return []

    counts: dict[str, int] = {}
    examples: dict[str, str] = {}
    no_cta = 0
    for post in texted_posts:
        label = classify_cta(post.caption_text)
        if label is None:
            no_cta += 1
            continue
        counts[label] = counts.get(label, 0) + 1
        examples.setdefault(label, _excerpt(post.caption_text, 80))

    total = len(texted_posts)
    lines = [
        f"{label} ({count}/{total} bài, {round(count / total * 100)}%) — vd: “{examples[label]}”"
        for label, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]

    no_cta_pct = round(no_cta / total * 100) if total else 0
    if no_cta == total:
        lines.append(
            f"Không có CTA rõ ràng trong {total}/{total} bài — nội dung mang tính thông tin hơn là chuyển đổi."
        )
    elif no_cta > 0:
        lines.append(f"{no_cta}/{total} bài ({no_cta_pct}%) không sử dụng CTA trực tiếp.")

    return lines
