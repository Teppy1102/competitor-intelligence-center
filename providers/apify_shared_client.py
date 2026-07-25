"""apify_shared_client.py - Sprint V3.3.2. Client Apify DUNG CHUNG cho MOI
extractor moi dung Apify (LinkedIn, TikTok, va bat ky nen tang nao sau nay) -
tach phan orchestration (run Actor, poll trang thai, timeout, retry, doc
Dataset) ra khoi logic mapping rieng cua tung nen tang.

Sprint V3.2 (providers/facebook_apify_provider.py) da chung minh dung pattern
nay o ApifyFacebookExtractor._call_actor_once() nhung viet RIENG (private
method, khong tai su dung duoc). Sprint V3.3.2 KHONG sua file do (de bai
"Khong pha Facebook Adapter hien tai") - thay vao do RUT RA thanh 1 module
dung chung MOI, LinkedIn/TikTok extractor (providers/linkedin_extractor.py,
providers/tiktok_extractor.py) goi module nay thay vi tu viet lai orchestration.

Nguyen tac giu nguyen tu Facebook provider (da kiem chung Sprint 2 Ver 2):
  - 1 lan goi actor().call() = DUNG 1 run, KHONG retry-loop vo han.
  - CHI retry 1 lan cho loi mang/server TAM THOI (ServerError,
    InvalidResponseBodyError, TimeoutError, ConnectionError, OSError).
  - KHONG retry loi input sai/quyen truy cap (InvalidRequestError,
    UnauthorizedError, ForbiddenError, NotFoundError) hoac Actor chay xong
    nhung that bai/Dataset rong - day la loi "thuc" can bao ngay, khong phai
    loi tam thoi.
  - max_items la co che GIOI HAN CUNG cua chinh Apify platform (Muc 17 "Gioi
    han so item de kiem soat chi phi") - khong phu thuoc dung dung ten field
    input cua tung Actor hay khong.
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

logger = logging.getLogger("cic.apify_shared")

DEFAULT_TIMEOUT_SECONDS = 180

_RETRYABLE_ERRORS = (ServerError, InvalidResponseBodyError, TimeoutError, ConnectionError, OSError)
_NON_RETRYABLE_ERRORS = (InvalidRequestError, UnauthorizedError, ForbiddenError, NotFoundError)


@dataclass(frozen=True)
class ApifyRunOutcome:
    """Ket qua 1 lan chay Actor - items RONG + error != None nghia la that
    bai (co the retry-able hay khong tuy nguyen nhan, caller khong can biet -
    da xu ly xong o day), items khong rong nghia la thanh cong (co the van
    it hon max_items neu Actor tra ve it hon yeu cau, KHONG phai loi)."""

    items: list[dict[str, Any]]
    error: str | None
    run_id: str | None
    dataset_id: str | None
    usage_usd: float | None


def redact_secret(value: str | None, *, keep_last: int = 4) -> str:
    """Che token/secret khi can dua vao log/thong bao loi - vd
    "abcd1234efgh" -> "********efgh". KHONG bao gio in nguyen token ra log
    (de bai Muc 7 "redact secret"). An toan voi None/chuoi rong/chuoi ngan
    hon keep_last (che toan bo, khong lo 1 phan)."""
    if not value:
        return ""
    if len(value) <= keep_last:
        return "*" * len(value)
    return "*" * (len(value) - keep_last) + value[-keep_last:]


class ApifyProviderConfigError(RuntimeError):
    """Loi cau hinh (thieu APIFY_API_TOKEN, actor_id rong...) - phan biet voi
    loi runtime cua 1 lan chay Actor (ApifyRunOutcome.error) de caller (vd
    linkedin_registry.py) co the bat rieng va tra ProviderConfigError dung
    ngu nghia (V3_ARCHITECTURE.md muc 8)."""


class ApifySharedClient:
    """Boc 1 ApifyClientAsync + APIFY_API_TOKEN DUY NHAT (de bai Muc 5/6:
    "Tai su dung Apify client va APIFY_API_TOKEN hien co", "Khong tao token
    rieng cho tung nen tang") - moi extractor (LinkedIn/TikTok) tu tao 1
    instance rieng cua class nay (giong Facebook tu tao ApifyClientAsync
    rieng), nhung TAT CA doc CUNG 1 bien moi truong APIFY_API_TOKEN, khong
    co bien APIFY_LINKEDIN_TOKEN/APIFY_TIKTOK_TOKEN nao duoc dinh nghia."""

    def __init__(self, *, api_token: str, client: Any = None) -> None:
        if not api_token:
            raise ApifyProviderConfigError(
                "Thiếu APIFY_API_TOKEN. Thêm dòng APIFY_API_TOKEN=... vào file .env "
                "(dùng chung với Facebook Provider - xem APIFY_SETUP_AND_TEST.md)."
            )
        # `client` cho phep test inject mock - production luon truyen None
        # (tu tao ApifyClientAsync that), giong pattern
        # ApifyFacebookExtractor.__init__ (providers/facebook_apify_provider.py).
        self._client = client if client is not None else ApifyClientAsync(api_token)
        self._token_redacted = redact_secret(api_token)

    async def run_actor_and_get_items(
        self,
        *,
        actor_id: str,
        run_input: dict[str, Any],
        max_items: int,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_total_charge_usd: Decimal | None = None,
        label: str = "actor",
    ) -> ApifyRunOutcome:
        """Chay 1 Actor (run + poll + doc Dataset) DUNG 1 LAN, toi da 1 retry
        cho loi mang/server tam thoi - xem quy tac retry o docstring dau file.
        KHONG bao gio raise ra ngoai (moi loi duoc gom vao ApifyRunOutcome.error)
        de caller (extractor) tu quyet dinh ExtractionStatus, dung nguyen tac
        "1 kenh loi khong lam sap ca run" (Muc 13)."""
        attempts_allowed = 2  # 1 lan chinh + TOI DA 1 lan retry
        last_error: str | None = None

        for attempt in range(1, attempts_allowed + 1):
            started_at = time.monotonic()
            try:
                run = await asyncio.wait_for(
                    self._client.actor(actor_id).call(
                        run_input=run_input,
                        max_items=max_items,
                        max_total_charge_usd=max_total_charge_usd,
                        run_timeout=None,
                        # apify_client.types.Timeout = timedelta | Literal[...] -
                        # KHONG truyen so nguyen tho (xem ghi chu tuong duong
                        # o providers/facebook_apify_provider.py - da xac
                        # nhan bang cach doc source apify_client).
                        timeout=timedelta(seconds=timeout_seconds),
                    ),
                    timeout=timeout_seconds,
                )
            except _NON_RETRYABLE_ERRORS as exc:
                logger.warning(
                    "apify_actor_input_error label=%s actor=%s status=%s attempt=%s token=%s",
                    label, actor_id, getattr(exc, "status_code", "?"), attempt, self._token_redacted,
                )
                return ApifyRunOutcome([], f"Lỗi cấu hình/quyền truy cập Apify ({label}): {exc}", None, None, None)
            except _RETRYABLE_ERRORS as exc:
                last_error = f"Lỗi mạng/máy chủ Apify tạm thời ({label}): {exc}"
                logger.warning(
                    "apify_actor_transient_error label=%s actor=%s attempt=%s detail=%s",
                    label, actor_id, attempt, exc,
                )
                if attempt < attempts_allowed:
                    await asyncio.sleep(1.5)
                    continue
                return ApifyRunOutcome([], last_error, None, None, None)
            except asyncio.TimeoutError:
                logger.warning("apify_actor_timeout label=%s actor=%s attempt=%s", label, actor_id, attempt)
                return ApifyRunOutcome(
                    [], f"Hết thời gian chờ Actor {label} (>{timeout_seconds}s).", None, None, None
                )
            except ApifyApiError as exc:
                logger.warning(
                    "apify_actor_api_error label=%s actor=%s status=%s attempt=%s",
                    label, actor_id, getattr(exc, "status_code", "?"), attempt,
                )
                return ApifyRunOutcome([], f"Lỗi Apify API ({label}): {exc}", None, None, None)

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
                # KHONG retry (day khong phai loi mang tam thoi).
                return ApifyRunOutcome(
                    [], f"Actor {label} kết thúc với trạng thái {status}.", run_id, dataset_id, usage_usd
                )

            if not dataset_id:
                return ApifyRunOutcome([], f"Actor {label} không trả Dataset.", run_id, None, usage_usd)

            try:
                items = await self.get_dataset_items(dataset_id, limit=max_items)
            except ApifyApiError as exc:
                return ApifyRunOutcome([], f"Không đọc được Dataset ({label}): {exc}", run_id, dataset_id, usage_usd)

            logger.info("apify_dataset_read label=%s run_id=%s item_count=%s", label, run_id, len(items))
            # Dataset rong - KHONG retry, tra ve rong de extractor tu quyet
            # dinh UNAVAILABLE/PARTIAL (giong Facebook - Muc 10 "Partial data").
            return ApifyRunOutcome(items, None, run_id, dataset_id, usage_usd)

        return ApifyRunOutcome([], last_error, None, None, None)

    async def get_dataset_items(self, dataset_id: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        """Doc truc tiep 1 Dataset da biet id - tach rieng khoi
        run_actor_and_get_items() de co the goi lai/kiem tra doc lap (vd
        debug 1 run da chay, hoac test)."""
        page = await self._client.dataset(dataset_id).list_items(limit=limit)
        return page.items or []
