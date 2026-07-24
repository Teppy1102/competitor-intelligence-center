"""Interface goi AI - Sprint 2 CHI dinh nghia hop dong, KHONG implement (yeu
cau Sprint 2 #7: khong goi API). Provider that (vd: OpenAI, port tu
MARKET_INTELLIGENCE_CENTER/providers/ai_provider.py) se implement class nay
o buoc sau, tuong tu cach Adapter implement PlatformAdapter (ARCHITECTURE.md
Sprint 1 muc 4).

AnalysisEngine (xem engine.py) CHI phu thuoc vao interface nay, khong bao
gio import truc tiep openai/httpx/... - dam bao analyzer/ khong goi API that
va co the test bang FakeAIClient (xem tests/, se viet o Sprint 4).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class AIClient(ABC):
    """Hop dong toi thieu de AnalysisEngine hoat dong. Provider that phai
    tu xu ly rieng: model fallback chain, retry, timeout, token limit -
    nhung ben ngoai interface nay deu khong biet chi tiet do (dung tinh
    than tach lop nhu Adapter Layer o ARCHITECTURE.md muc 3.1)."""

    @abstractmethod
    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        """Goi AI va tra ve text response THO (ky vong la HTML voi 13 <h2>
        danh so theo REPORT_SPECIFICATION_V1.md Muc 15). Khong parse/validate
        o day - report/parser.py (package khac) chiu trach nhiem do.

        Phai raise loi co y nghia (vd AIClientError ben duoi) neu that bai -
        AnalysisEngine khong tu doan loi tu ket qua rong/None.
        """
        raise NotImplementedError


class AIClientError(RuntimeError):
    """Loi chung khi goi AI that bai (timeout, rate limit, model tu choi...).
    Provider implementation nen wrap loi cu the (vd openai.APIError) thanh
    loi nay truoc khi de AnalysisEngine bat duoc, giu AnalysisEngine khong
    phu thuoc vao thu vien AI cu the nao."""
