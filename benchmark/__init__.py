"""benchmark/ - Benchmark Engine (Competitor Intelligence Center, Sprint 2)

Sprint 2 yeu cau #4: "Thiet ke Benchmark Engine (chua implement so sanh
LinkPower, chi dinh nghia interface)". Package nay gom:

- interface.py  - BenchmarkEngine (ABC, CHUA implement compare())
- eligibility.py - cong kiem tra du lieu toi thieu (DA implement - day la
  phep kiem tra nguong, khong phai "logic so sanh")
- rules.py       - luoi an toan enforce Muc 12 (DA implement, tuong tu
  engine/rules.py cua MIC)

benchmark/ CHI phu thuoc schemas/ - khong import analyzer/ hay report/ (xem
ly do o interface.py) de tranh circular import, vi analyzer/prompt_builder.py
can goi is_benchmark_eligible() tu day.
"""

from .eligibility import benchmark_ineligibility_reason, is_benchmark_eligible
from .interface import BenchmarkDraft, BenchmarkEngine
from .rule_based import StatsBenchmarkEngine
from .rules import enforce_benchmark_rules

__all__ = [
    "BenchmarkEngine",
    "BenchmarkDraft",
    "is_benchmark_eligible",
    "benchmark_ineligibility_reason",
    "enforce_benchmark_rules",
    "StatsBenchmarkEngine",
]
