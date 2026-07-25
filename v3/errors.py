"""errors.py - Sprint V3.2. Exception dung chung cho toan bo v3/services/*,
de v3/routers_v3.py bat 1 lan duy nhat va tra HTTP status + response dang
thong nhat (V3_ARCHITECTURE.md muc 8 "Error Handling", de bai muc 15
"Error response thong nhat").
"""

from __future__ import annotations


class V3Error(Exception):
    """Lop goc - moi loi nghiep vu Ver 3 deu ke thua tu day de router phan
    biet duoc voi loi he thong khong luong truoc (Exception thuan)."""

    http_status: int = 400


class NotFoundError(V3Error):
    http_status = 404


class ProjectNotFoundError(NotFoundError):
    pass


class BrandNotFoundError(NotFoundError):
    pass


class ChannelNotFoundError(NotFoundError):
    pass


class JobNotFoundError(NotFoundError):
    pass


class BenchmarkRunNotFoundError(NotFoundError):
    pass


class ReportNotFoundError(NotFoundError):
    pass


class UnsupportedPlatformError(V3Error):
    """URL hop le nhung khong thuoc Facebook/LinkedIn/TikTok/YouTube da biet -
    xem v3/platform_detector.py."""

    http_status = 400


class InvalidImportFileError(V3Error):
    """File CSV/JSON Manual Import sai cau truc, qua kich thuoc, hoac chua
    noi dung nguy hiem (CSV formula injection...) - xem
    v3/services/import_service.py."""

    http_status = 400


class DuplicateRunError(V3Error):
    """Chan tao benchmark run trung khi user bam nhieu lan lien tiep -
    idempotency cho POST /benchmark/projects/:id/run (de bai muc 15)."""

    http_status = 409


class IdempotencyKeyConflictError(V3Error):
    """Client gui lai 1 Idempotency-Key DA DUNG truoc do nhung voi payload
    KHAC - Sprint V3.3.4 de bai muc 2.3 ("Cùng key nhưng payload khác phải
    trả lỗi rõ ràng"). 422 (khong phai 409 - 409 da dung cho DuplicateRunError
    o tren, 2 loi nay mang y nghia khac nhau: 409 la "co 1 job dang chay",
    422 la "request khong hop le vi tai su dung key sai cach")."""

    http_status = 422
