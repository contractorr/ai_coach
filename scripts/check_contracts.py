"""Verify that exported API contracts are in sync with the backend schema."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PROFILE_PACKAGE = SRC / "profile"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if "profile" in sys.modules and not hasattr(sys.modules["profile"], "__path__"):
    del sys.modules["profile"]
profile_spec = importlib.util.spec_from_file_location(
    "profile",
    PROFILE_PACKAGE / "__init__.py",
    submodule_search_locations=[str(PROFILE_PACKAGE)],
)
assert profile_spec and profile_spec.loader
profile_module = importlib.util.module_from_spec(profile_spec)
sys.modules["profile"] = profile_module
profile_spec.loader.exec_module(profile_module)


OPENAPI_PATH = Path("web/openapi.json")
GENERATED_TYPES_PATH = Path("web/src/types/api.generated.ts")
HASH_PATTERN = re.compile(r"^// OpenAPI SHA256: ([0-9a-f]{64})$", re.MULTILINE)


def _expected_openapi_text() -> str | None:
    try:
        from web.app import app
    except ModuleNotFoundError:
        return None

    return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


def main() -> int:
    errors: list[str] = []
    expected_openapi_text = _expected_openapi_text()
    expected_hash: str | None = None

    if expected_openapi_text is not None:
        expected_hash = hashlib.sha256(expected_openapi_text.encode("utf-8")).hexdigest()

    if not OPENAPI_PATH.exists():
        errors.append(f"Missing exported schema: {OPENAPI_PATH}")
    else:
        current_openapi_text = OPENAPI_PATH.read_text(encoding="utf-8")
        if expected_openapi_text is not None and current_openapi_text != expected_openapi_text:
            errors.append(
                f"{OPENAPI_PATH} is stale. Run `just contracts-generate` after backend contract changes."
            )
        else:
            expected_hash = hashlib.sha256(OPENAPI_PATH.read_bytes()).hexdigest()

    if not GENERATED_TYPES_PATH.exists():
        errors.append(f"Missing generated frontend types: {GENERATED_TYPES_PATH}")
    else:
        generated_text = GENERATED_TYPES_PATH.read_text(encoding="utf-8")
        match = HASH_PATTERN.search(generated_text)
        if not match:
            errors.append(
                f"{GENERATED_TYPES_PATH} is missing the OpenAPI hash header. "
                "Regenerate with `just contracts-generate`."
            )
        elif match.group(1) != expected_hash:
            errors.append(
                f"{GENERATED_TYPES_PATH} is stale for the current schema. "
                "Run `just contracts-generate`."
            )

    if errors:
        for error in errors:
            print(error)
        return 1

    if expected_openapi_text is None:
        print("OpenAPI export and generated frontend types are internally in sync.")
        print("Backend schema verification skipped because app dependencies are unavailable.")
    else:
        print("OpenAPI export and generated frontend types are in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
