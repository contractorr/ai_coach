"""Guardrails for the spec-driven development harness."""

import re
from pathlib import Path

import yaml

CATALOG_PATH = Path("specs/catalog.yaml")
MANIFEST_PATH = Path("specs/manifest.yaml")
FUNCTIONAL_DIR = Path("specs/functional")
FUNCTIONAL_ARCHIVE_DIR = FUNCTIONAL_DIR / "archive"
TECHNICAL_DIR = Path("specs/technical")
TECHNICAL_ARCHIVE_DIR = TECHNICAL_DIR / "archive"
FOUNDATIONS_DIR = Path("specs/foundations")
IGNORED_SPEC_FILES = {"INDEX.md", "TEMPLATE.md"}


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_markdown_frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    assert match, f"{path} is missing YAML frontmatter"
    return yaml.safe_load(match.group(1))


def _active_spec_files(root: Path) -> set[str]:
    return {path.as_posix() for path in root.glob("*.md") if path.name not in IGNORED_SPEC_FILES}


def _archived_spec_files(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {path.as_posix() for path in root.glob("*.md")}


def _tracked_feature_paths(catalog: dict) -> set[str]:
    return {payload["path"] for payload in catalog["functional_specs"]["tracked_features"].values()}


def _tracked_module_paths(catalog: dict) -> set[str]:
    return {payload["path"] for payload in catalog["technical_specs"]["tracked_modules"].values()}


def _catalog_paths(catalog: dict) -> set[str]:
    paths = set(catalog["canonical_artifacts"].values())
    paths.update(catalog["foundations"])
    paths.update(_tracked_feature_paths(catalog))
    paths.update(catalog["functional_specs"]["supporting"])
    paths.update(catalog["functional_specs"]["archived"])
    for payload in catalog["functional_specs"]["tracked_features"].values():
        paths.update(payload.get("technical_specs", []))
        paths.update(payload.get("foundations", []))
    paths.update(_tracked_module_paths(catalog))
    paths.update(catalog["technical_specs"]["supporting"])
    paths.update(catalog["technical_specs"]["archived"])
    for payload in catalog["technical_specs"]["tracked_modules"].values():
        paths.update(payload.get("code_paths", []))
        for feature_id in payload.get("implements", []):
            assert isinstance(feature_id, str)
    return paths


def test_spec_catalog_exists_and_has_expected_sections():
    catalog = _load_yaml(CATALOG_PATH)

    assert catalog["version"] >= 1
    assert isinstance(catalog["canonical_artifacts"], dict)
    assert isinstance(catalog["foundations"], list)
    assert isinstance(catalog["functional_specs"]["tracked_features"], dict)
    assert isinstance(catalog["functional_specs"]["supporting"], list)
    assert isinstance(catalog["technical_specs"]["tracked_modules"], dict)
    assert isinstance(catalog["technical_specs"]["supporting"], list)
    assert set(catalog["lifecycle_statuses"]) == {
        "tracked_features",
        "tracked_modules",
    }


def test_catalog_paths_exist():
    catalog = _load_yaml(CATALOG_PATH)
    missing = sorted(path for path in _catalog_paths(catalog) if not Path(path).exists())
    assert missing == []


def test_every_active_functional_spec_is_catalogued():
    catalog = _load_yaml(CATALOG_PATH)
    expected = _active_spec_files(FUNCTIONAL_DIR)
    actual = _tracked_feature_paths(catalog) | set(catalog["functional_specs"]["supporting"])

    assert actual == expected
    assert set(catalog["functional_specs"]["archived"]) == _archived_spec_files(
        FUNCTIONAL_ARCHIVE_DIR
    )


def test_every_active_technical_spec_is_catalogued():
    catalog = _load_yaml(CATALOG_PATH)
    expected = _active_spec_files(TECHNICAL_DIR)
    actual = _tracked_module_paths(catalog) | set(catalog["technical_specs"]["supporting"])

    assert actual == expected
    assert set(catalog["technical_specs"]["archived"]) == _archived_spec_files(
        TECHNICAL_ARCHIVE_DIR
    )


def test_every_foundation_doc_is_catalogued():
    catalog = _load_yaml(CATALOG_PATH)
    expected = {path.as_posix() for path in FOUNDATIONS_DIR.glob("*.md")}
    assert set(catalog["foundations"]) == expected


def test_manifest_features_are_backed_by_catalog_entries():
    catalog = _load_yaml(CATALOG_PATH)
    manifest = _load_yaml(MANIFEST_PATH)
    tracked_features = catalog["functional_specs"]["tracked_features"]

    assert set(manifest["features"]).issubset(tracked_features)

    for feature_id, payload in manifest["features"].items():
        catalog_entry = tracked_features[feature_id]
        assert payload["functional_spec"] == catalog_entry["path"]
        assert payload.get("technical_specs", []) == catalog_entry.get("technical_specs", [])


def test_tracked_feature_docs_have_machine_readable_frontmatter():
    catalog = _load_yaml(CATALOG_PATH)

    for feature_id, payload in catalog["functional_specs"]["tracked_features"].items():
        frontmatter = _load_markdown_frontmatter(Path(payload["path"]))
        assert frontmatter["id"] == feature_id
        assert frontmatter["category"] == "tracked_feature"
        assert frontmatter["status"] == payload["status"]
        assert frontmatter["technical_specs"] == payload.get("technical_specs", [])
        assert frontmatter["foundations"] == payload.get("foundations", [])


def test_tracked_module_docs_have_machine_readable_frontmatter():
    catalog = _load_yaml(CATALOG_PATH)

    for module_id, payload in catalog["technical_specs"]["tracked_modules"].items():
        frontmatter = _load_markdown_frontmatter(Path(payload["path"]))
        assert frontmatter["id"] == module_id
        assert frontmatter["category"] == "tracked_module"
        assert frontmatter["status"] == payload["status"]
        assert frontmatter["implements"] == payload.get("implements", [])
        assert frontmatter["code_paths"] == payload.get("code_paths", [])


def test_catalog_lists_are_sorted_and_non_overlapping():
    catalog = _load_yaml(CATALOG_PATH)

    assert catalog["foundations"] == sorted(catalog["foundations"])
    assert catalog["functional_specs"]["supporting"] == sorted(
        catalog["functional_specs"]["supporting"]
    )
    assert catalog["technical_specs"]["supporting"] == sorted(
        catalog["technical_specs"]["supporting"]
    )

    tracked_features = _tracked_feature_paths(catalog)
    tracked_modules = _tracked_module_paths(catalog)

    assert tracked_features.isdisjoint(catalog["functional_specs"]["supporting"])
    assert tracked_modules.isdisjoint(catalog["technical_specs"]["supporting"])


def test_tracked_module_implementations_reference_known_features():
    catalog = _load_yaml(CATALOG_PATH)
    tracked_features = set(catalog["functional_specs"]["tracked_features"])

    for payload in catalog["technical_specs"]["tracked_modules"].values():
        assert set(payload.get("implements", [])).issubset(tracked_features)
