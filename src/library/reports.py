"""Markdown-backed storage for Library items."""

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import frontmatter


def _now() -> str:
    return datetime.now().isoformat()


def _slug(text: str) -> str:
    slug = text.lower().strip().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    return slug[:60] or "report"


def _format_file_size(file_size: int | None) -> str:
    if not file_size or file_size < 0:
        return ""
    units = ["B", "KB", "MB", "GB"]
    value = float(file_size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return ""


class ReportStore:
    """Manages Library items stored as markdown metadata plus optional attachments."""

    def __init__(self, library_dir: str | Path):
        self.library_dir = Path(library_dir).expanduser().resolve()
        self.library_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir = self._validate_path(self.library_dir / "attachments")
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_dir = self._validate_path(self.library_dir / "extracted")
        self.extracted_dir.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, path: Path) -> Path:
        resolved = path.resolve()
        if not resolved.is_relative_to(self.library_dir):
            raise ValueError(f"Path escapes library directory: {path}")
        return resolved

    def _filename(self, title: str) -> Path:
        date_str = datetime.now().strftime("%Y-%m-%d")
        base = f"{date_str}_{_slug(title)}"
        candidate = self._validate_path(self.library_dir / f"{base}.md")
        counter = 1
        while candidate.exists():
            candidate = self._validate_path(self.library_dir / f"{base}_{counter}.md")
            counter += 1
        return candidate

    def _attachment_filename(self, report_id: str, suffix: str) -> Path:
        suffix = suffix if suffix.startswith(".") else f".{suffix}"
        return self._validate_path(self.attachments_dir / f"{report_id}{suffix.lower()}")

    def _extracted_text_filename(self, report_id: str) -> Path:
        return self._validate_path(self.extracted_dir / f"{report_id}.txt")

    def _load_extracted_text(self, post: frontmatter.Post) -> str:
        extracted_text_path = post.get("extracted_text_path")
        if not extracted_text_path:
            return ""
        try:
            path = self._validate_path(self.library_dir / extracted_text_path)
            if path.exists() and path.is_file():
                return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError, ValueError):
            return ""
        return ""

    def _post_to_record(self, path: Path, post: frontmatter.Post) -> dict:
        content = post.content or ""
        extracted_text = self._load_extracted_text(post)
        preview = content[:240] or extracted_text[:240]
        file_name = post.get("file_name")
        file_size = post.get("file_size")
        if not preview and file_name:
            file_size_label = _format_file_size(file_size)
            preview = f"Uploaded PDF: {file_name}"
            if file_size_label:
                preview = f"{preview} ({file_size_label})"

        return {
            "id": post.get("report_id") or path.stem,
            "path": str(path),
            "title": post.get("title", path.stem),
            "report_type": post.get("report_type", "custom"),
            "status": post.get("status", "ready"),
            "collection": post.get("collection"),
            "prompt": post.get("prompt", ""),
            "source_kind": post.get("source_kind", "generated"),
            "created": post.get("created") or post.get("updated") or _now(),
            "updated": post.get("updated") or post.get("created") or _now(),
            "last_generated_at": post.get("last_generated_at")
            or post.get("updated")
            or post.get("created")
            or _now(),
            "preview": preview,
            "content": content,
            "file_name": file_name,
            "file_size": file_size,
            "mime_type": post.get("mime_type"),
            "has_attachment": bool(post.get("attachment_path")),
            "attachment_path": post.get("attachment_path"),
            "extraction_status": post.get("extraction_status"),
            "extracted_text_path": post.get("extracted_text_path"),
            "has_extracted_text": bool(extracted_text.strip()),
            "origin_surface": post.get("origin_surface", "library"),
            "visibility_state": post.get("visibility_state", "saved"),
            "index_status": post.get("index_status") or post.get("extraction_status") or "ready",
            "extracted_chars": len(extracted_text or ""),
        }

    def create(
        self,
        *,
        title: str,
        prompt: str,
        report_type: str,
        content: str,
        collection: str | None = None,
        source_kind: str = "generated",
        status: str = "ready",
    ) -> dict:
        now = _now()
        post = frontmatter.Post(content)
        post["report_id"] = str(uuid.uuid4())
        post["title"] = title
        post["report_type"] = report_type
        post["status"] = status
        post["collection"] = collection
        post["prompt"] = prompt
        post["source_kind"] = source_kind
        post["created"] = now
        post["updated"] = now
        post["last_generated_at"] = now
        path = self._filename(title)
        path.write_text(frontmatter.dumps(post), encoding="utf-8")
        return self._post_to_record(path, post)

    def create_uploaded_pdf(
        self,
        *,
        title: str,
        file_name: str,
        file_bytes: bytes,
        mime_type: str = "application/pdf",
        collection: str | None = None,
        extracted_text: str = "",
        extraction_status: str = "pending",
        origin_surface: str = "library",
        visibility_state: str = "saved",
        index_status: str | None = None,
    ) -> dict:
        now = _now()
        report_id = str(uuid.uuid4())
        attachment_path = self._attachment_filename(report_id, ".pdf")
        attachment_path.write_bytes(file_bytes)

        post = frontmatter.Post("")
        post["report_id"] = report_id
        post["title"] = title
        post["report_type"] = "document"
        post["status"] = "ready"
        post["collection"] = collection
        post["prompt"] = f"Uploaded PDF: {file_name}"
        post["source_kind"] = "uploaded_pdf"
        post["file_name"] = file_name
        post["file_size"] = len(file_bytes)
        post["mime_type"] = mime_type
        post["attachment_path"] = str(attachment_path.relative_to(self.library_dir))
        post["extraction_status"] = extraction_status
        post["origin_surface"] = origin_surface
        post["visibility_state"] = visibility_state
        post["index_status"] = index_status or extraction_status
        post["created"] = now
        post["updated"] = now
        post["last_generated_at"] = now

        if extracted_text.strip():
            extracted_path = self._extracted_text_filename(report_id)
            extracted_path.write_text(extracted_text, encoding="utf-8")
            post["extracted_text_path"] = str(extracted_path.relative_to(self.library_dir))

        path = self._filename(title)
        path.write_text(frontmatter.dumps(post), encoding="utf-8")
        return self._post_to_record(path, post)

    def list_reports(
        self,
        *,
        search: str | None = None,
        status: str | None = None,
        collection: str | None = None,
        limit: int = 50,
        include_hidden: bool = False,
    ) -> list[dict]:
        query = (search or "").strip().lower()
        normalized_collection = (collection or "").strip().lower()
        records: list[dict] = []
        for path in self.library_dir.glob("*.md"):
            try:
                post = frontmatter.load(path)
            except (OSError, ValueError):
                continue
            record = self._post_to_record(path, post)
            if not include_hidden and record.get("visibility_state") == "hidden":
                continue
            if status and record["status"] != status:
                continue
            if (
                normalized_collection
                and (record.get("collection") or "").strip().lower() != normalized_collection
            ):
                continue
            if query:
                haystack = "\n".join(
                    [
                        record["title"],
                        record.get("prompt") or "",
                        record.get("collection") or "",
                        record.get("file_name") or "",
                        record.get("preview") or "",
                    ]
                ).lower()
                if query not in haystack:
                    continue
            records.append(record)
        records.sort(key=lambda item: item.get("updated") or "", reverse=True)
        return records[:limit]

    def get_report(self, report_id: str) -> dict | None:
        for path in self.library_dir.glob("*.md"):
            try:
                post = frontmatter.load(path)
            except (OSError, ValueError):
                continue
            if post.get("report_id") == report_id:
                return self._post_to_record(path, post)
        return None

    def get_attachment_path(self, report_id: str) -> Path | None:
        record = self.get_report(report_id)
        attachment_path = (record or {}).get("attachment_path")
        if not attachment_path:
            return None
        try:
            path = self._validate_path(self.library_dir / attachment_path)
        except ValueError:
            return None
        if not path.exists() or not path.is_file():
            return None
        return path

    def get_extracted_text(self, report_id: str) -> str:
        for path in self.library_dir.glob("*.md"):
            try:
                post = frontmatter.load(path)
            except (OSError, ValueError):
                continue
            if post.get("report_id") == report_id:
                return self._load_extracted_text(post)
        return ""

    def update_report(
        self,
        report_id: str,
        *,
        title: Optional[str] = None,
        content: Optional[str] = None,
        collection: Optional[str] = None,
        status: Optional[str] = None,
        last_generated_at: Optional[str] = None,
        extraction_status: Optional[str] = None,
        visibility_state: Optional[str] = None,
        index_status: Optional[str] = None,
    ) -> dict | None:
        for path in self.library_dir.glob("*.md"):
            try:
                post = frontmatter.load(path)
            except (OSError, ValueError):
                continue
            if post.get("report_id") != report_id:
                continue
            if title is not None:
                post["title"] = title
            if collection is not None:
                post["collection"] = collection
            if status is not None:
                post["status"] = status
            if content is not None:
                post.content = content
            if last_generated_at is not None:
                post["last_generated_at"] = last_generated_at
            if extraction_status is not None:
                post["extraction_status"] = extraction_status
            if visibility_state is not None:
                post["visibility_state"] = visibility_state
            if index_status is not None:
                post["index_status"] = index_status
            post["updated"] = _now()
            path.write_text(frontmatter.dumps(post), encoding="utf-8")
            return self._post_to_record(path, post)
        return None

    def archive_report(self, report_id: str) -> dict | None:
        return self.update_report(report_id, status="archived")

    def restore_report(self, report_id: str) -> dict | None:
        return self.update_report(report_id, status="ready")
