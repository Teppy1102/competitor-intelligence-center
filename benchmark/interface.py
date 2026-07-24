"""BenchmarkEngine - interface CHUA IMPLEMENT logic so sanh (dung yeu cau
Sprint 2 #4). Day la phan quan trong nhat cua report (REPORT_SPECIFICATION_
V1.md Sprint 1 dat ten section 12 la "quan trong nhat") nen duoc tach thanh
1 interface rieng, testable doc lap, thay vi chon vui trong Analysis Engine
chung (xem ghi chu thiet ke o benchmark/__init__.py).

Quan he voi phan con lai cua he thong (KHONG doi kien truc da duyet - chi
lam ro o muc code):
- analyzer/ (Sprint nay) sinh ra ban nhap 13 section (gom ca section 12) tu
  1 lan goi AI DUY NHAT, dung PROMPT_DESIGN.md ("1 prompt duy nhat sinh toan
  bo 13 section"). Ban nhap Benchmark do LA MOT DAU VAO cho BenchmarkEngine
  ben duoi, khong phai output cuoi cung.
- BenchmarkEngine.compare() (Sprint sau, khi co Adapter va du lieu that) se
  quyet dinh: dung nguyen ban nhap AI, lam giau them bang logic
  rule-based, hoac goi rieng 1 AI call tap trung cho Benchmark - Sprint 2
  CHUA quyet dinh cach nao, chi dinh nghia contract dau vao/dau ra.
- benchmark/rules.py (da implement) la buoc enforce SAU CUNG, doc lap voi
  compare() lam gi ben trong - luon chay de dam bao khong bao gio tra
  Benchmark "bia" khi thieu du lieu, bat ke BenchmarkEngine cu the nao dang
  duoc dung.

benchmark/ CHI phu thuoc schemas/ - khong import analyzer/ hay report/, de
tranh circular import (analyzer/ moi la ben phu thuoc benchmark/, khong
nguoc lai - xem analyzer/prompt_builder.py).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from schemas import BenchmarkSection, CompetitorDataset


@dataclass(frozen=True)
class BenchmarkDraft:
    """Ban nhap section 12 do AnalysisEngine (analyzer/) sinh ra tu 1 lan
    goi AI chung - la 1 trong cac dau vao co the co cua compare(), CHUA
    chac chan se dung truc tiep (xem docstring module)."""

    ai_drafted_section: BenchmarkSection | None
    """None neu dataset khong du dieu kien de AI thu viet Benchmark (xem
    analyzer/completeness.py eligibility.benchmark tuong duong -
    is_benchmark_eligible o eligibility.py cua chinh package nay)."""


class BenchmarkEngine(ABC):
    """Hop dong DUY NHAT ma phan con lai cua he thong duoc phep goi.
    Implementation cu the (rule-based thuan tuy, AI-assisted, hoac ket hop)
    se viet o Sprint sau - Sprint 2 CHI dinh nghia interface nay va de trong
    than (NotImplementedError), dung yeu cau #4 cua Sprint 2.
    """

    @abstractmethod
    def compare(
        self,
        dataset: CompetitorDataset,
        draft: BenchmarkDraft | None = None,
    ) -> BenchmarkSection:
        """Tra ve BenchmarkSection HOAN CHINH (rows, linkpower_advantages,
        competitor_advantages, gap_analysis, quick_wins, content_gap - dung
        schema REPORT_SPECIFICATION_V1.md Muc 12).

        Khong duoc tu goi API/AI ben trong ham nay (benchmark/ khong phu
        thuoc analyzer/ hay bat ky HTTP client nao) - neu implementation
        that can goi AI, phai nhan AIClient (xem analyzer/ai_client.py) qua
        constructor cua class con, KHONG import truc tiep tu analyzer/.

        Luu y cho nguoi implement o Sprint sau: KHONG tu kiem tra
        is_benchmark_eligible() roi bo qua neu khong du du lieu - viec do da
        co benchmark/rules.py.enforce_benchmark_rules() lam SAU KHI ham nay
        tra ve, de dam bao luoi an toan hoat dong bat ke compare() implement
        the nao. compare() cu viet ket qua "tot nhat co the" voi du lieu co
        san; enforce_benchmark_rules() se ghi de neu can.
        """
        raise NotImplementedError
