"""FastAPI app cho Competitor Intelligence Center - Facebook MVP.

Endpoint chinh (khong doi route - theo dung yeu cau):
  POST /api/competitor/facebook   { "url": "..." }
  -> tra ve CompetitorReport day du (JSON, do Report Generator sinh ra).

`time_range` van duoc CHAP NHAN trong request (client cu con gui) nhung la
field DEPRECATED - KHONG duoc dung de loc du lieu, khong bao gio gay loi du
gia tri gi (xem engine/pipeline.py). MVP hien tai luon phan tich toi da
FACEBOOK_POST_LIMIT (30) bai gan nhat, khong con khai niem khoang thoi gian.

Dong bo (khong job_id/polling) - phu hop pham vi MVP: 1 lan bam nut "Phan
tich" tren edu.linkpower.vn/research cho ra ket qua ngay ben duoi, khong
chuyen trang (dung yeu cau PHAN 3 cua de bai). Van luu job (.json/.html/
.meta.json) qua engine/jobs.py de phuc vu logging/audit (PHAN 7) va lam nen
cho polling neu Sprint sau can chuyen sang bat dong bo.

Facebook Provider production MAC DINH la Apify (khong con Playwright) - xem
providers/registry.py.get_facebook_extractor(): chon dua theo bien moi truong
FACEBOOK_PROVIDER (mac dinh "apify"). File nay TUYET DOI khong import
providers.facebook_playwright_provider hay providers.facebook_fixture_provider
o cap module - Playwright chi duoc import LAZY ben trong registry.py khi
quan tri vien chu dong dat FACEBOOK_PROVIDER=playwright, va Fixture Provider
chi duoc dung trong tests/ (khong bao gio duoc production import).

KHONG doi/xoa bat ky package da lock kien truc nao (schemas/, analyzer/,
benchmark/, report/) - main.py chi wire cac package do lai voi nhau qua
engine/pipeline.py.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from adapters import FacebookAdapter
from engine.pipeline import PipelineError, run_facebook_analysis
from providers.ai_provider import get_ai_client
from providers.registry import ProviderConfigError, get_facebook_extractor

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

with open(BASE_DIR / "config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("cic.main")

app = FastAPI(title="Competitor Intelligence Center - Facebook MVP")

# CORS - API cong khai, khong dung cookie/session, cho phep goi tu Ladipage
# (edu.linkpower.vn) - dung dung tinh than da thong nhat o Market
# Intelligence Center (frontend khong phu thuoc backend, khac domain).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class FacebookAnalyzeRequest(BaseModel):
    url: str
    time_range: str | None = Field(
        default=None,
        deprecated=True,
        description=(
            "DEPRECATED - khong con duoc su dung de loc du lieu. MVP hien tai "
            "luon phan tich toi da 30 bai gan nhat. Field nay CHI con de tuong "
            "thich nguoc voi client cu, gia tri (neu co) se bi bo qua hoan toan."
        ),
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "Competitor Intelligence Center API",
        "active_platforms": CONFIG.get("active_platforms", []),
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


@app.post("/api/competitor/facebook")
async def analyze_facebook(req: FacebookAnalyzeRequest):
    url = (req.url or "").strip()
    if not url:
        raise HTTPException(400, "URL không được để trống")

    # get_facebook_extractor() chon Apify (mac dinh) hoac Playwright (CHI khi
    # FACEBOOK_PROVIDER=playwright duoc dat thu cong) - KHONG co nhanh nao
    # chon FixtureFacebookExtractor o day, dam bao production khong bao gio
    # "am tham" dung du lieu gia lap (yeu cau goc #8) va khong tu dong
    # fallback giua Apify/Playwright (yeu cau moi Muc 2).
    try:
        extractor = get_facebook_extractor(CONFIG)
    except ProviderConfigError as exc:
        logger.error("provider_config_error detail=%s", exc)
        raise HTTPException(500, str(exc))

    adapter = FacebookAdapter(extractor=extractor)
    if not adapter.detect(url):
        raise HTTPException(
            400,
            "URL không phải Fanpage Facebook hợp lệ. Sprint hiện tại chỉ hỗ trợ Facebook "
            "(LinkedIn/TikTok/YouTube sẽ hỗ trợ ở giai đoạn sau).",
        )

    if req.time_range:
        logger.warning("deprecated_time_range_field_received value=%r url=%s", req.time_range, url)

    try:
        ai_client = get_ai_client()
    except RuntimeError as exc:
        logger.error("config_error detail=%s", exc)
        raise HTTPException(500, str(exc))

    try:
        result = await run_facebook_analysis(
            competitor_url=url,
            time_range_label_raw=req.time_range,
            reports_dir=REPORTS_DIR,
            config=CONFIG,
            adapter=adapter,
            ai_client=ai_client,
        )
    except PipelineError as exc:
        logger.warning("analyze_failed url=%s detail=%s", url, exc)
        raise HTTPException(422, str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("analyze_unexpected_error url=%s", url)
        raise HTTPException(502, f"Lỗi hệ thống không mong muốn: {exc}")

    return result.report_json


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3001)
