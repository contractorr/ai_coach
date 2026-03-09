"""Tests for Library report routes."""

import web.routes.library as library_routes


def _sample_pdf_bytes(text: str) -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R >> endobj\n"
        + f"4 0 obj << /Length 64 >> stream\nBT /F1 12 Tf 40 100 Td ({text}) Tj ET\nendstream endobj\n".encode()
        + b"xref\n0 5\n0000000000 65535 f \ntrailer << /Root 1 0 R /Size 5 >>\nstartxref\n0\n%%EOF\n"
    )


def test_create_list_update_and_archive_report(client, auth_headers):
    library_routes._generate_report_content = (
        lambda user_id,
        prompt,
        report_type: f"# Generated\n\nPrompt: {prompt}\n\nType: {report_type}"
    )
    try:
        create_res = client.post(
            "/api/library/reports",
            headers=auth_headers,
            json={
                "prompt": "Give me a crash course on the insurance industry",
                "report_type": "crash_course",
                "collection": "Industries",
            },
        )
        assert create_res.status_code == 201
        created = create_res.json()
        assert created["report_type"] == "crash_course"
        assert created["status"] == "ready"
        assert created["collection"] == "Industries"
        assert "insurance industry" in created["content"].lower()

        list_res = client.get("/api/library/reports?search=insurance", headers=auth_headers)
        assert list_res.status_code == 200
        listing = list_res.json()
        assert len(listing) == 1
        assert listing[0]["id"] == created["id"]

        update_res = client.put(
            f"/api/library/reports/{created['id']}",
            headers=auth_headers,
            json={
                "title": "Insurance Crash Course",
                "content": "# Edited",
                "collection": "Research",
            },
        )
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["title"] == "Insurance Crash Course"
        assert updated["content"] == "# Edited"
        assert updated["collection"] == "Research"

        archive_res = client.post(
            f"/api/library/reports/{created['id']}/archive",
            headers=auth_headers,
        )
        assert archive_res.status_code == 200
        assert archive_res.json()["status"] == "archived"

        archived_list = client.get("/api/library/reports?status=archived", headers=auth_headers)
        assert archived_list.status_code == 200
        assert len(archived_list.json()) == 1

        restore_res = client.post(
            f"/api/library/reports/{created['id']}/restore",
            headers=auth_headers,
        )
        assert restore_res.status_code == 200
        assert restore_res.json()["status"] == "ready"
    finally:
        from importlib import reload

        reload(library_routes)


def test_upload_pdf_is_searchable_and_downloadable(client, auth_headers):
    response = client.post(
        "/api/library/reports/upload",
        headers=auth_headers,
        data={"collection": "Career"},
        files={
            "file": (
                "resume.pdf",
                _sample_pdf_bytes("Raj Contractor CV Python leadership fintech"),
                "application/pdf",
            )
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["source_kind"] == "uploaded_pdf"
    assert created["has_attachment"] is True
    assert created["has_extracted_text"] is True
    assert created["extraction_status"] == "ready"

    search_res = client.get("/api/library/reports?search=leadership", headers=auth_headers)
    assert search_res.status_code == 200
    listing = search_res.json()
    assert len(listing) == 1
    assert listing[0]["id"] == created["id"]
    assert "leadership" in listing[0]["preview"].lower()

    file_res = client.get(f"/api/library/reports/{created['id']}/file", headers=auth_headers)
    assert file_res.status_code == 200
    assert file_res.content.startswith(b"%PDF-")
    assert file_res.headers["content-type"].startswith("application/pdf")


def test_refresh_rejects_uploaded_pdf(client, auth_headers):
    upload_res = client.post(
        "/api/library/reports/upload",
        headers=auth_headers,
        files={"file": ("resume.pdf", _sample_pdf_bytes("resume text"), "application/pdf")},
    )
    assert upload_res.status_code == 201
    report_id = upload_res.json()["id"]

    refresh_res = client.post(f"/api/library/reports/{report_id}/refresh", headers=auth_headers)
    assert refresh_res.status_code == 400
    assert "generated reports" in refresh_res.json()["detail"].lower()


def test_refresh_preserves_report_identity(client, auth_headers):
    calls = []

    def fake_generate(user_id, prompt, report_type):
        calls.append((user_id, prompt, report_type))
        return f"# Version {len(calls)}"

    library_routes._generate_report_content = fake_generate
    try:
        create_res = client.post(
            "/api/library/reports",
            headers=auth_headers,
            json={"prompt": "Summarize fintech infrastructure", "report_type": "overview"},
        )
        created = create_res.json()

        refresh_res = client.post(
            f"/api/library/reports/{created['id']}/refresh",
            headers=auth_headers,
        )
        assert refresh_res.status_code == 200
        refreshed = refresh_res.json()
        assert refreshed["id"] == created["id"]
        assert refreshed["content"] == "# Version 2"
        assert len(calls) == 2
    finally:
        from importlib import reload

        reload(library_routes)


def test_library_reports_are_user_scoped(client, auth_headers, auth_headers_b):
    library_routes._generate_report_content = (
        lambda user_id, prompt, report_type: "# Private report"
    )
    try:
        create_res = client.post(
            "/api/library/reports",
            headers=auth_headers,
            json={"prompt": "Create a private memo", "report_type": "memo"},
        )
        report_id = create_res.json()["id"]

        other_user_get = client.get(f"/api/library/reports/{report_id}", headers=auth_headers_b)
        assert other_user_get.status_code == 404

        other_user_list = client.get("/api/library/reports", headers=auth_headers_b)
        assert other_user_list.status_code == 200
        assert other_user_list.json() == []
    finally:
        from importlib import reload

        reload(library_routes)
