"""engine/ - Orchestration layer (Competitor Intelligence Center)

Phan con thieu sau Sprint 2 de he thong "chay duoc that": noi ghep
adapters/ (thu thap) + analyzer/ (phan tich AI) + benchmark/ (so sanh) +
report/ (tong hop) thanh 1 luong end-to-end cho 1 request phan tich Facebook,
cong voi luu tru job (giong pattern engine/jobs.py cua MIC).

- pipeline.py - run_facebook_analysis(): dieu phoi toan bo luong
- jobs.py     - job store file-based (.json/.meta.json), dung cho logging/
  audit va (neu can sau nay) polling - khong dung Database, giong MIC.
"""

from .jobs import create_job, get_job, list_jobs, mark_completed, mark_failed, new_job_id
from .pipeline import PipelineError, run_facebook_analysis

__all__ = [
    "run_facebook_analysis",
    "PipelineError",
    "new_job_id",
    "create_job",
    "mark_completed",
    "mark_failed",
    "get_job",
    "list_jobs",
]
