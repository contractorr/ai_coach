import frontmatter

from library.reports import ReportStore


def test_list_reports_skips_invalid_extracted_text_path(tmp_path):
    store = ReportStore(tmp_path / "library")
    record = store.create(title="Resume", prompt="p" * 10, report_type="memo", content="Body")

    path = next(store.library_dir.glob("*.md"))
    post = frontmatter.load(path)
    post["extracted_text_path"] = "../escape.txt"
    path.write_text(frontmatter.dumps(post), encoding="utf-8")

    reports = store.list_reports()

    assert len(reports) == 1
    assert reports[0]["id"] == record["id"]
    assert reports[0]["has_extracted_text"] is False
    assert reports[0]["extracted_chars"] == 0


def test_list_reports_ignores_non_utf8_extracted_text(tmp_path):
    store = ReportStore(tmp_path / "library")
    record = store.create(title="Resume", prompt="p" * 10, report_type="memo", content="Body")

    extracted_path = store.extracted_dir / f"{record['id']}.txt"
    extracted_path.write_bytes(b"\xff\xfe\x00\x00")

    path = next(store.library_dir.glob("*.md"))
    post = frontmatter.load(path)
    post["extracted_text_path"] = str(extracted_path.relative_to(store.library_dir))
    path.write_text(frontmatter.dumps(post), encoding="utf-8")

    reports = store.list_reports()

    assert len(reports) == 1
    assert reports[0]["id"] == record["id"]
    assert reports[0]["has_extracted_text"] is False
    assert reports[0]["extracted_chars"] == 0


def test_get_attachment_path_returns_none_for_escaped_metadata_path(tmp_path):
    store = ReportStore(tmp_path / "library")
    record = store.create_uploaded_pdf(
        title="Resume",
        file_name="resume.pdf",
        file_bytes=b"%PDF-1.4\n",
    )

    path = next(store.library_dir.glob("*.md"))
    post = frontmatter.load(path)
    post["attachment_path"] = "../escape.pdf"
    path.write_text(frontmatter.dumps(post), encoding="utf-8")

    assert store.get_attachment_path(record["id"]) is None
