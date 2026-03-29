"""Export the FastAPI OpenAPI schema for frontend contract generation."""

from __future__ import annotations

import argparse
import importlib.util
import json
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


def _canonical_schema_text() -> str:
    from web.app import app

    schema = app.openapi()
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="Path to the exported OpenAPI JSON file.")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_canonical_schema_text(), encoding="utf-8")


if __name__ == "__main__":
    main()
