"""Guardrails for the machine-readable repo feature manifest."""

from pathlib import Path

MANIFEST_PATH = Path("specs/manifest.yaml")
PATH_FIELDS = ("functional_spec",)
MULTI_PATH_FIELDS = ("technical_specs", "backend", "frontend", "tests")


def _load_manifest() -> dict:
    import yaml

    return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_manifest_exists_and_has_feature_entries():
    manifest = _load_manifest()
    assert manifest["version"] >= 1
    assert isinstance(manifest["features"], dict)
    assert manifest["features"]


def test_manifest_paths_exist():
    manifest = _load_manifest()
    missing = []
    for feature_name, payload in manifest["features"].items():
        for field in PATH_FIELDS:
            candidate = Path(payload[field])
            if not candidate.exists():
                missing.append(f"{feature_name}.{field}: {candidate}")
        for field in MULTI_PATH_FIELDS:
            for raw_path in payload.get(field, []):
                candidate = Path(raw_path)
                if not candidate.exists():
                    missing.append(f"{feature_name}.{field}: {candidate}")
    assert missing == []


def test_manifest_validation_commands_are_present():
    manifest = _load_manifest()
    offenders = []
    for feature_name, payload in manifest["features"].items():
        commands = payload.get("validation_commands") or []
        if not commands or any(not command.strip() for command in commands):
            offenders.append(feature_name)
    assert offenders == []
