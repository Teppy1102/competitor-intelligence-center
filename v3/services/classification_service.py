"""classification_service.py - Sprint V3.2 (de bai muc 10 "AI Content
Classification").

Dung lai analyzer.AIClient interface (KHONG viet AI client moi - tai su
dung providers.ai_provider.get_ai_client() cua Ver 2). Prompt yeu cau JSON
co cau truc (khac HTML 13-<h2> cua analyzer/prompt_builder.py danh cho
Facebook MVP report) - validate bang whitelist gia tri cho phep, retry DUNG
1 LAN neu JSON sai schema (dung nguyen tac da co o
engine/pipeline.py._analyze_with_retry_and_fallback cua Ver 2), fallback
rule-based (khong AI) neu van loi hoac khong co AIClient kha dung.

Nguyen tac bat bien: MOI normalized_item LUON co 1 ban ghi
content_classifications sau khi chay ham o day - khong bao gio bo trong,
`classified_by` ghi ro "ai" hay "rule_fallback" de report/frontend hien
thi dung do tin cay (de bai muc 10: "Phai co validation va retry khi output
sai schema").
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3

from analyzer import AIClient, AIClientError

from v3 import repository as repo

logger = logging.getLogger("cic.v3.classification")

CONTENT_PILLARS = [
    "educational", "product_or_course", "case_study", "event", "branding",
    "corporate_culture", "recruitment", "market_news", "social_proof", "promotion", "other",
]
FUNNEL_STAGES = ["awareness", "consideration", "conversion", "retention_or_community"]
CONTENT_INTENTS = ["educate", "build_authority", "engage", "sell", "generate_leads", "recruit", "announce"]
FORMATS = ["text", "image", "carousel", "video", "short_video", "livestream", "document", "external_link"]

_CONTENT_TYPE_TO_FORMAT = {
    "video": "video", "reel_short": "short_video", "image": "image",
    "carousel": "carousel", "text": "text", "link": "external_link",
}
_CTA_KEYWORDS = (
    "đăng ký", "liên hệ", "tìm hiểu thêm", "mua ngay", "xem thêm", "nhắn tin",
    "gọi ngay", "để lại thông tin", "click", "inbox",
)

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _looks_like_cta(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(kw in lowered for kw in _CTA_KEYWORDS)


def _build_prompt(item: dict) -> tuple[str, str]:
    system_prompt = (
        "Bạn là chuyên gia phân loại nội dung mạng xã hội cho ngành đào tạo "
        "doanh nghiệp B2B tại Việt Nam. Trả lời DUY NHẤT bằng 1 JSON object hợp "
        "lệ, không thêm văn bản nào khác, không dùng markdown code fence.\n"
        f'content_pillar phải là 1 trong: {CONTENT_PILLARS}.\n'
        f'funnel_stage phải là 1 trong: {FUNNEL_STAGES}.\n'
        f'content_intent phải là 1 trong: {CONTENT_INTENTS}.\n'
        f'format phải là 1 trong: {FORMATS}.\n'
        "Các trường primary_message, target_audience, pain_point, benefit, "
        "cta_type, tone_of_voice, product_mentioned là text ngắn tiếng Việt "
        "(hoặc null nếu không đủ căn cứ trong nội dung - TUYỆT ĐỐI KHÔNG bịa). "
        "confidence là số thực 0-1 tự đánh giá độ chắc chắn."
    )
    user_prompt = (
        f"Nền tảng: {item.get('platform')}\n"
        f"Loại nội dung (đã biết chắc, không cần đoán lại): {item.get('content_type')}\n"
        f"Caption: {item.get('text_content') or '(rỗng)'}\n"
        f"Hashtag: {', '.join(item.get('hashtags') or []) or '(không có)'}\n"
    )
    return system_prompt, user_prompt


def _parse_json(raw: str) -> dict:
    text = (raw or "").strip()
    text = _JSON_FENCE_RE.sub("", text).strip()
    return json.loads(text)


def _validate(data: dict) -> dict:
    pillar = data.get("content_pillar")
    if pillar not in CONTENT_PILLARS:
        raise ValueError(f"content_pillar không hợp lệ: {pillar!r}")
    stage = data.get("funnel_stage")
    if stage not in FUNNEL_STAGES:
        raise ValueError(f"funnel_stage không hợp lệ: {stage!r}")
    intent = data.get("content_intent")
    if intent not in CONTENT_INTENTS:
        raise ValueError(f"content_intent không hợp lệ: {intent!r}")
    fmt = data.get("format")
    if fmt not in FORMATS:
        raise ValueError(f"format không hợp lệ: {fmt!r}")

    try:
        confidence = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))

    return {
        "content_pillar": pillar,
        "funnel_stage": stage,
        "content_intent": intent,
        "format": fmt,
        "primary_message": data.get("primary_message"),
        "target_audience": data.get("target_audience"),
        "pain_point": data.get("pain_point"),
        "benefit": data.get("benefit"),
        "cta_type": data.get("cta_type"),
        "tone_of_voice": data.get("tone_of_voice"),
        "product_mentioned": data.get("product_mentioned"),
        "confidence": confidence,
    }


def rule_based_classification(item: dict) -> dict:
    """KHONG AI - chi dua tren du lieu THAT da co san (content_type, tu khoa
    CTA co ban) - content_pillar luon "other" (khong the phan loai chu de
    chinh xac ma khong co AI, KHONG doan bua), cac truong dinh tinh de None
    thay vi bia."""
    fmt = _CONTENT_TYPE_TO_FORMAT.get(item.get("content_type") or "text", "text")
    return {
        "content_pillar": "other",
        "funnel_stage": "awareness",
        "content_intent": "engage",
        "format": fmt,
        "primary_message": None,
        "target_audience": None,
        "pain_point": None,
        "benefit": None,
        "cta_type": "has_cta" if _looks_like_cta(item.get("text_content")) else None,
        "tone_of_voice": None,
        "product_mentioned": None,
        "confidence": 0.0,
        "classified_by": "rule_fallback",
    }


async def classify_item(ai_client: AIClient, item: dict) -> dict:
    last_error: Exception | None = None
    for attempt in (1, 2):
        try:
            system_prompt, user_prompt = _build_prompt(item)
            raw = await ai_client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
            validated = _validate(_parse_json(raw))
            validated["classified_by"] = "ai"
            return validated
        except (AIClientError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            logger.warning(
                "classification_ai_failed item_id=%s attempt=%s detail=%s",
                item.get("id"), attempt, exc,
            )
            continue

    logger.error(
        "classification_ai_failed_after_retry item_id=%s last_error=%s - dùng rule-based fallback",
        item.get("id"), last_error,
    )
    return rule_based_classification(item)


async def classify_project_items(
    conn: sqlite3.Connection, project_id: str, ai_client: AIClient | None
) -> list[dict]:
    """Phan loai TOAN BO normalized_items cua 1 project. `ai_client=None`
    (vd thieu OPENAI_API_KEY) -> dung rule-based cho MOI item, KHONG thu
    goi AI (tranh cho vo ich/timeout lap lai)."""
    items = repo.list_normalized_items_by_project(conn, project_id)
    results = []
    for item in items:
        if ai_client is not None:
            classification = await classify_item(ai_client, item)
        else:
            classification = rule_based_classification(item)
        classification["normalized_item_id"] = item["id"]
        results.append(repo.upsert_classification(conn, classification))
    return results
