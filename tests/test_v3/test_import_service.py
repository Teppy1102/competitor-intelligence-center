import pytest

from v3.errors import InvalidImportFileError
from v3.services import import_service as imp


def _csv(rows: str) -> bytes:
    header = "external_content_id,text_content,like_count\n"
    return (header + rows).encode("utf-8")


def test_parse_csv_valid_rows():
    content = _csv("post-1,Nội dung A,10\npost-2,Nội dung B,20\n")
    result = imp.parse_import_file(filename="x.csv", content=content)
    assert result.valid_count == 2
    assert result.invalid_count == 0


def test_parse_csv_rejects_missing_required_field():
    content = _csv(",Nội dung A,10\n")
    result = imp.parse_import_file(filename="x.csv", content=content)
    assert result.invalid_count == 1
    assert "external_content_id" in result.row_results[0].errors[0]


def test_parse_json_accepts_items_wrapper():
    content = b'{"items": [{"external_content_id": "p1", "text_content": "abc"}]}'
    result = imp.parse_import_file(filename="x.json", content=content)
    assert result.valid_count == 1


def test_parse_json_rejects_non_list_non_items_object():
    content = b'{"foo": "bar"}'
    with pytest.raises(InvalidImportFileError):
        imp.parse_import_file(filename="x.json", content=content)


def test_parse_json_rejects_malformed_json():
    with pytest.raises(InvalidImportFileError):
        imp.parse_import_file(filename="x.json", content=b"{not valid json")


def test_parse_rejects_unsupported_extension():
    with pytest.raises(InvalidImportFileError):
        imp.parse_import_file(filename="x.txt", content=b"external_content_id,text_content\na,b\n")


def test_parse_rejects_oversized_file():
    huge = b"x" * (imp.MAX_IMPORT_FILE_BYTES + 1)
    with pytest.raises(InvalidImportFileError):
        imp.parse_import_file(filename="x.csv", content=huge)


def test_parse_rejects_empty_file():
    with pytest.raises(InvalidImportFileError):
        imp.parse_import_file(filename="x.csv", content=b"")


def test_parse_rejects_too_many_rows():
    rows = "".join(f"p{i},text{i},1\n" for i in range(imp.MAX_IMPORT_ROWS + 1))
    with pytest.raises(InvalidImportFileError):
        imp.parse_import_file(filename="x.csv", content=_csv(rows))


def test_sanitize_value_neutralizes_formula_injection():
    assert imp._sanitize_value("=SUM(A1:A2)").startswith("'")
    assert imp._sanitize_value("+1+1").startswith("'")
    assert imp._sanitize_value("@cmd").startswith("'")
    assert imp._sanitize_value("nội dung bình thường") == "nội dung bình thường"


def test_split_list_field_handles_pipe_separator():
    assert imp._split_list_field("#a|#b|#c") == ["#a", "#b", "#c"]
    assert imp._split_list_field(None) == []
    assert imp._split_list_field("") == []


def test_commit_import_persists_and_creates_batch(v3_conn):
    from v3 import repository as repo

    conn = v3_conn
    project = repo.create_project(conn, name="Test")
    brand = repo.create_brand(conn, project_id=project["id"], name="LP", brand_type="linkpower")
    channel = repo.create_channel(
        conn, project_id=project["id"], brand_id=brand["id"], platform="linkedin",
        source_url="https://linkedin.com/company/x", normalized_url="https://linkedin.com/company/x",
    )
    content = _csv("post-1,Nội dung A,10\n")
    parse_result = imp.parse_import_file(filename="x.csv", content=content)
    result = imp.commit_import(
        conn, channel_id=channel["id"], project_id=project["id"], brand_id=brand["id"],
        platform="linkedin", filename="x.csv", file_format="csv", valid_rows=parse_result.valid_rows,
    )
    assert result["batch"]["row_count"] == 1
    assert len(repo.list_normalized_items(conn, channel["id"])) == 1
    assert repo.list_normalized_items(conn, channel["id"])[0]["provider"] == "manual_import"
