"""ReportGenerator - orchestrator DUY NHAT ma phan con lai cua he thong nen
goi tu package report/. Ghep report/parser.py + report/rules.py +
report/renderer.py thanh 1 buoc, nhan dau vao la RawAnalysisResult (tu
analyzer/, package khac cung viet o Sprint nay).

Luu tru file (.html/.json/.meta.json, giong pattern jobs.py cua MIC) va
routers/ FastAPI CHUA nam trong pham vi Sprint 2 nay (yeu cau #6, #7: khong
Adapter, khong goi API - viec luu tru/goi qua HTTP se noi vao khi wiring
pipeline that o buoc sau). ReportGenerator.generate() chi tra ve object -
noi goi no quyet dinh luu o dau.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from analyzer import RawAnalysisResult
from schemas import CompetitorReport

from .parser import parse_report
from .renderer import ReportMeta, render_report_html
from .rules import enforce_anti_fabrication_rules


@dataclass(frozen=True)
class GeneratedReport:
    """Dau ra cuoi cung - san sang de luu (jobs.py, chua viet Sprint nay) va
    tra ve cho client (routers/, chua viet Sprint nay)."""

    report: CompetitorReport
    html: str
    job_id: str
    prompt_version: str
    schema_version: str
    generated_at: datetime


class ReportGenerator:
    """Khong giu state giua cac lan goi - an toan dung lai cho nhieu job
    song song (khong nhu AnalysisEngine can inject AIClient, ReportGenerator
    khong can dependency nao ca vi khong goi API)."""

    def generate(self, analysis: RawAnalysisResult, job_id: str) -> GeneratedReport:
        """Co the raise report.parser.ReportParseError neu HTML AI tra ve
        thieu section bat buoc - noi goi ham nay (pipeline, chua viet Sprint
        nay) chiu trach nhiem retry theo WORKFLOW.md Sprint 1 muc 3."""
        parsed = parse_report(analysis.raw_html)
        final_report = enforce_anti_fabrication_rules(
            parsed, analysis.dataset, analysis.stats
        )

        generated_at = datetime.now(timezone.utc)
        meta = ReportMeta(
            job_id=job_id,
            prompt_version=analysis.prompt_version,
            schema_version=analysis.dataset.schema_version,
            generated_at=generated_at,
        )
        html = render_report_html(final_report, analysis.dataset, meta)

        return GeneratedReport(
            report=final_report,
            html=html,
            job_id=job_id,
            prompt_version=analysis.prompt_version,
            schema_version=analysis.dataset.schema_version,
            generated_at=generated_at,
        )
