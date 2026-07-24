"""report/ - Report Generator (Competitor Intelligence Center, Sprint 2)

Sprint 2 yeu cau #3: "Thiet ke Report Generator". Package nay gom:

- parser.py    - HTML (AI tra ve) -> schemas.CompetitorReport (best-effort,
  dung Report Markup Convention v1 - xem docstring parser.py)
- rules.py     - Enforce anti-fabrication SAU parse (ghi de bang du lieu
  that/da tinh san, uy quyen phan Benchmark cho benchmark/rules.py)
- renderer.py  - Render CompetitorReport -> 1 trang HTML tinh de luu/tai ve
- generator.py - ReportGenerator, orchestrator DUY NHAT nen goi tu ben ngoai

report/ phu thuoc schemas/, benchmark/ (qua rules.py) va analyzer/ (chi de
lay kieu du lieu RawAnalysisResult/DatasetStatsBundle - KHONG goi lai
AnalysisEngine, tranh nham lan trach nhiem giua 2 package).
"""

from .generator import GeneratedReport, ReportGenerator
from .parser import RawSection, ReportParseError, parse_report, parse_sections
from .renderer import ReportMeta, render_report_html
from .rules import enforce_anti_fabrication_rules

__all__ = [
    "ReportGenerator",
    "GeneratedReport",
    "parse_report",
    "parse_sections",
    "RawSection",
    "ReportParseError",
    "render_report_html",
    "ReportMeta",
    "enforce_anti_fabrication_rules",
]
