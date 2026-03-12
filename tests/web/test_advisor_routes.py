"""Tests for advisor API routes (ask, streaming, conversations)."""

import time
from types import SimpleNamespace
from unittest.mock import patch


def _sample_pdf_bytes(text: str) -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R >> endobj\n"
        + f"4 0 obj << /Length 64 >> stream\nBT /F1 12 Tf 40 100 Td ({text}) Tj ET\nendstream endobj\n".encode()
        + b"xref\n0 5\n0000000000 65535 f \ntrailer << /Root 1 0 R /Size 5 >>\nstartxref\n0\n%%EOF\n"
    )


def _mock_get_engine(user_id, use_tools=False):
    """Return a mock AdvisorEngine that returns canned answers."""

    def _ask(
        question,
        advice_type="general",
        conversation_history=None,
        attachment_ids=None,
        event_callback=None,
    ):
        if event_callback:
            event_callback({"type": "tool_start", "tool": "journal_search"})
            event_callback({"type": "tool_done", "tool": "journal_search", "is_error": False})
        suffix = f" using {len(attachment_ids or [])} attachment(s)" if attachment_ids else ""
        return f"Mock advice for: {question}{suffix}"

    class _Engine:
        def ask(self, *args, **kwargs):
            return _ask(*args, **kwargs)

        def ask_result(self, *args, **kwargs):
            question = args[0] if args else kwargs.get("question", "")
            used = "decide" in question.lower()
            return SimpleNamespace(
                answer=_ask(*args, **kwargs),
                council_used=used,
                council_member_count=2 if used else 0,
                council_providers=["claude", "openai"] if used else [],
                council_failed_providers=[],
                council_partial=False,
            )

    engine = _Engine()
    return engine


_ENGINE_PATCH = "web.routes.advisor._get_engine"


def _upload_pdf(client, auth_headers, text="Raj Contractor Python leadership"):
    res = client.post(
        "/api/library/reports/upload",
        headers=auth_headers,
        files={"file": ("resume.pdf", _sample_pdf_bytes(text), "application/pdf")},
    )
    assert res.status_code == 201
    return res.json()


def test_ask_returns_answer(client, auth_headers):
    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        res = client.post(
            "/api/advisor/ask",
            headers=auth_headers,
            json={"question": "What should I do?"},
        )
    assert res.status_code == 200
    data = res.json()
    assert "Mock advice" in data["answer"]
    assert data["advice_type"] == "general"
    assert "conversation_id" in data


def test_ask_failure_cleans_up_new_conversation(client, auth_headers):
    class _BrokenEngine:
        def ask_result(self, *args, **kwargs):
            raise RuntimeError("engine failed")

    with patch(_ENGINE_PATCH, return_value=_BrokenEngine()):
        res = client.post(
            "/api/advisor/ask",
            headers=auth_headers,
            json={"question": "What should I do?"},
        )

    assert res.status_code == 500
    assert client.get("/api/advisor/conversations", headers=auth_headers).json() == []


def test_ask_failure_cleans_up_only_failed_user_turn(client, auth_headers):
    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        first = client.post(
            "/api/advisor/ask",
            headers=auth_headers,
            json={"question": "First"},
        )
    conv_id = first.json()["conversation_id"]

    class _BrokenEngine:
        def ask_result(self, *args, **kwargs):
            raise RuntimeError("engine failed")

    with patch(_ENGINE_PATCH, return_value=_BrokenEngine()):
        failed = client.post(
            "/api/advisor/ask",
            headers=auth_headers,
            json={"question": "Second", "conversation_id": conv_id},
        )

    assert failed.status_code == 500
    detail = client.get(f"/api/advisor/conversations/{conv_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert [message["content"] for message in detail.json()["messages"]] == [
        "First",
        "Mock advice for: First",
    ]


def test_ask_returns_council_metadata_for_decision_prompt(client, auth_headers):
    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        res = client.post(
            "/api/advisor/ask",
            headers=auth_headers,
            json={"question": "Help me decide what I should do next"},
        )

    assert res.status_code == 200
    data = res.json()
    assert data["council_used"] is True
    assert data["council_member_count"] == 2
    assert data["council_providers"] == ["claude", "openai"]


def test_ask_creates_conversation(client, auth_headers):
    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        res = client.post(
            "/api/advisor/ask",
            headers=auth_headers,
            json={"question": "Test question"},
        )
    conv_id = res.json()["conversation_id"]
    assert conv_id

    res2 = client.get(f"/api/advisor/conversations/{conv_id}", headers=auth_headers)
    assert res2.status_code == 200
    messages = res2.json()["messages"]
    assert len(messages) == 2
    # message_id exposed for both user and assistant messages
    assert all(msg["id"] for msg in messages)


def test_ask_with_existing_conversation(client, auth_headers):
    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        res1 = client.post(
            "/api/advisor/ask",
            headers=auth_headers,
            json={"question": "First"},
        )
        conv_id = res1.json()["conversation_id"]

        res2 = client.post(
            "/api/advisor/ask",
            headers=auth_headers,
            json={"question": "Second", "conversation_id": conv_id},
        )
    assert res2.json()["conversation_id"] == conv_id

    detail = client.get(f"/api/advisor/conversations/{conv_id}", headers=auth_headers)
    assert len(detail.json()["messages"]) == 4


def test_ask_persists_attachment_metadata(client, auth_headers):
    report = _upload_pdf(client, auth_headers)

    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        res = client.post(
            "/api/advisor/ask",
            headers=auth_headers,
            json={
                "question": "Use my CV for this answer",
                "attachment_ids": [report["id"]],
            },
        )

    assert res.status_code == 200
    assert "1 attachment" in res.json()["answer"]

    conv_id = res.json()["conversation_id"]
    detail = client.get(f"/api/advisor/conversations/{conv_id}", headers=auth_headers)
    assert detail.status_code == 200
    first_message = detail.json()["messages"][0]
    assert first_message["attachments"] == [
        {
            "library_item_id": report["id"],
            "file_name": report["file_name"],
            "mime_type": report["mime_type"],
        }
    ]


def test_ask_rejects_unknown_attachment(client, auth_headers):
    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        res = client.post(
            "/api/advisor/ask",
            headers=auth_headers,
            json={"question": "Use my CV", "attachment_ids": ["missing-doc"]},
        )
    assert res.status_code == 404
    assert "attachment not found" in res.json()["detail"].lower()


def test_ask_stream_sse_events(client, auth_headers):
    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        res = client.post(
            "/api/advisor/ask/stream",
            headers=auth_headers,
            json={"question": "Stream me"},
        )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("content-type", "")

    events = []
    for line in res.text.strip().split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            import json

            events.append(json.loads(line[6:]))

    types = [event["type"] for event in events]
    assert "tool_start" in types
    assert "tool_done" in types
    assert "answer" in types

    answer_event = next(event for event in events if event["type"] == "answer")
    assert "conversation_id" in answer_event
    assert "Mock advice" in answer_event["content"]
    assert answer_event["council_used"] is False


def test_ask_stream_includes_council_metadata(client, auth_headers):
    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        res = client.post(
            "/api/advisor/ask/stream",
            headers=auth_headers,
            json={"question": "Help me decide between two options"},
        )

    assert res.status_code == 200
    events = []
    for line in res.text.strip().split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            import json

            events.append(json.loads(line[6:]))

    answer_event = next(event for event in events if event["type"] == "answer")
    assert answer_event["council_used"] is True
    assert answer_event["council_providers"] == ["claude", "openai"]


def test_ask_stream_emits_message_id(client, auth_headers):
    """Non-agentic path: answer event includes message_id directly."""
    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        res = client.post(
            "/api/advisor/ask/stream",
            headers=auth_headers,
            json={"question": "Give me the id"},
        )
    assert res.status_code == 200
    events = []
    for line in res.text.strip().split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            import json

            events.append(json.loads(line[6:]))

    answer_event = next(event for event in events if event["type"] == "answer")
    assert answer_event.get("message_id"), "answer event should contain message_id"


def test_ask_stream_emits_message_persisted_for_agentic(client, auth_headers):
    """Agentic path: answer sent before persist -> message_persisted event follows."""

    class _AgenticEngine:
        def ask_result(
            self,
            question,
            advice_type="general",
            conversation_history=None,
            attachment_ids=None,
            event_callback=None,
        ):
            # Simulate agentic: fire answer event BEFORE returning
            if event_callback:
                event_callback({"type": "answer", "content": f"Agentic: {question}"})
            return SimpleNamespace(
                answer=f"Agentic: {question}",
                council_used=False,
                council_member_count=0,
                council_providers=[],
                council_failed_providers=[],
                council_partial=False,
            )

    with patch(_ENGINE_PATCH, return_value=_AgenticEngine()):
        res = client.post(
            "/api/advisor/ask/stream",
            headers=auth_headers,
            json={"question": "Agentic test"},
        )
    assert res.status_code == 200
    events = []
    for line in res.text.strip().split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            import json

            events.append(json.loads(line[6:]))

    types = [e["type"] for e in events]
    assert "answer" in types
    assert "message_persisted" in types
    persisted = next(e for e in events if e["type"] == "message_persisted")
    assert persisted.get("message_id"), "message_persisted should contain message_id"


def test_ask_stream_failure_cleans_up_new_conversation(client, auth_headers):
    class _BrokenEngine:
        def ask_result(self, *args, **kwargs):
            raise RuntimeError("stream failed")

    with patch(_ENGINE_PATCH, return_value=_BrokenEngine()):
        res = client.post(
            "/api/advisor/ask/stream",
            headers=auth_headers,
            json={"question": "Stream failure"},
        )

    assert res.status_code == 200
    assert "stream failed" in res.text
    assert client.get("/api/advisor/conversations", headers=auth_headers).json() == []


def test_ask_stream_disconnect_still_persists_assistant_turn(client, auth_headers):
    class _SlowEngine:
        def ask_result(
            self,
            question,
            advice_type="general",
            conversation_history=None,
            attachment_ids=None,
            event_callback=None,
        ):
            if event_callback:
                event_callback({"type": "tool_start", "tool": "journal_search"})
            time.sleep(0.1)
            return SimpleNamespace(
                answer=f"Slow advice for: {question}",
                council_used=False,
                council_member_count=0,
                council_providers=[],
                council_failed_providers=[],
                council_partial=False,
            )

    with patch(_ENGINE_PATCH, return_value=_SlowEngine()):
        with client.stream(
            "POST",
            "/api/advisor/ask/stream",
            headers=auth_headers,
            json={"question": "Disconnect me"},
        ) as response:
            assert response.status_code == 200
            first_data_line = next(response.iter_lines())
            assert "tool_start" in first_data_line

    conversation_id = None
    expected_messages = ["Disconnect me", "Slow advice for: Disconnect me"]
    for _ in range(20):
        conversations = client.get("/api/advisor/conversations", headers=auth_headers).json()
        if conversations:
            conversation_id = conversations[0]["id"]
            detail = client.get(
                f"/api/advisor/conversations/{conversation_id}",
                headers=auth_headers,
            ).json()
            if [message["content"] for message in detail["messages"]] == expected_messages:
                break
        time.sleep(0.05)

    assert conversation_id is not None
    detail = client.get(f"/api/advisor/conversations/{conversation_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert [message["content"] for message in detail.json()["messages"]] == expected_messages


def test_conversations_crud(client, auth_headers):
    res = client.get("/api/advisor/conversations", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []

    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        ask_res = client.post(
            "/api/advisor/ask",
            headers=auth_headers,
            json={"question": "Hello"},
        )
    conv_id = ask_res.json()["conversation_id"]

    res = client.get("/api/advisor/conversations", headers=auth_headers)
    assert len(res.json()) == 1

    res = client.get(f"/api/advisor/conversations/{conv_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == conv_id

    res = client.delete(f"/api/advisor/conversations/{conv_id}", headers=auth_headers)
    assert res.status_code == 200

    res = client.get("/api/advisor/conversations", headers=auth_headers)
    assert res.json() == []


def test_conversation_isolation(client, auth_headers, auth_headers_b):
    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        res = client.post(
            "/api/advisor/ask",
            headers=auth_headers,
            json={"question": "Private question"},
        )
    conv_id = res.json()["conversation_id"]

    res = client.get(f"/api/advisor/conversations/{conv_id}", headers=auth_headers_b)
    assert res.status_code == 404

    res = client.delete(f"/api/advisor/conversations/{conv_id}", headers=auth_headers_b)
    assert res.status_code == 404

    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        res = client.post(
            "/api/advisor/ask",
            headers=auth_headers_b,
            json={"question": "Hijack", "conversation_id": conv_id},
        )
    assert res.status_code == 404


def test_attachment_is_user_scoped(client, auth_headers, auth_headers_b):
    report = _upload_pdf(client, auth_headers)

    with patch(_ENGINE_PATCH, side_effect=_mock_get_engine):
        res = client.post(
            "/api/advisor/ask",
            headers=auth_headers_b,
            json={"question": "Use someone else's CV", "attachment_ids": [report["id"]]},
        )
    assert res.status_code == 404


def test_chat_attachment_upload_rejects_non_pdf(client, auth_headers):
    res = client.post(
        "/api/advisor/attachments",
        headers=auth_headers,
        files={"file": ("notes.txt", b"plain text", "text/plain")},
    )

    assert res.status_code == 400
    assert "pdf" in res.json()["detail"].lower()


def test_chat_attachment_upload_returns_hidden_ready_attachment(client, auth_headers):
    res = client.post(
        "/api/advisor/attachments",
        headers=auth_headers,
        files={
            "file": (
                "resume.pdf",
                _sample_pdf_bytes("Raj Contractor Python leadership"),
                "application/pdf",
            )
        },
    )

    assert res.status_code == 200
    data = res.json()
    assert data["attachment_id"]
    assert data["index_status"] == "ready"
    assert data["visibility_state"] == "hidden"
    assert data["warning"] is None

    library_res = client.get("/api/library/reports", headers=auth_headers)
    assert library_res.status_code == 200
    assert library_res.json() == []


def test_chat_attachment_upload_warns_when_text_extraction_is_limited(client, auth_headers):
    res = client.post(
        "/api/advisor/attachments",
        headers=auth_headers,
        files={"file": ("scan.pdf", _sample_pdf_bytes(""), "application/pdf")},
    )

    assert res.status_code == 200
    data = res.json()
    assert data["index_status"] == "limited_text"
    assert data["warning"] == "Limited text extracted from PDF."


def test_chat_attachment_can_be_saved_to_library(client, auth_headers):
    upload_res = client.post(
        "/api/advisor/attachments",
        headers=auth_headers,
        files={
            "file": (
                "resume.pdf",
                _sample_pdf_bytes("Raj Contractor Python leadership"),
                "application/pdf",
            )
        },
    )
    attachment = upload_res.json()

    save_res = client.post(
        f"/api/advisor/attachments/{attachment['attachment_id']}/save",
        headers=auth_headers,
    )

    assert save_res.status_code == 200
    saved = save_res.json()
    assert saved["attachment_id"] == attachment["attachment_id"]
    assert saved["visibility_state"] == "saved"

    library_res = client.get("/api/library/reports", headers=auth_headers)
    assert library_res.status_code == 200
    listing = library_res.json()
    assert len(listing) == 1
    assert listing[0]["id"] == attachment["attachment_id"]
    assert listing[0]["visibility_state"] == "saved"
