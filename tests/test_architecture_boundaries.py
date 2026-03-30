"""Architecture guardrail tests for package dependency boundaries."""

from pathlib import Path

FORBIDDEN_DOMAIN_IMPORT_PREFIXES = ("cli.", "web.")
DOMAIN_ROOTS = ("advisor", "intelligence", "research", "services")
SURFACE_ROOTS = ("web/routes", "cli/commands", "coach_mcp/tools")
FORBIDDEN_SURFACE_IMPORT_PREFIXES = ("web.routes", "cli.commands", "coach_mcp.tools")
DOCUMENTED_ROOTS = (
    Path("src/advisor"),
    Path("src/curriculum"),
    Path("src/intelligence"),
    Path("src/memory"),
    Path("src/web"),
    Path("web/src"),
    Path("tests"),
)
HOTSPOT_LINE_BUDGETS = {
    Path("src/web/routes/curriculum.py"): 2700,
    Path("src/curriculum/store.py"): 1800,
    Path("src/memory/store.py"): 1100,
    Path("src/web/models.py"): 1125,
    Path("src/advisor/recommendations.py"): 825,
    Path("web/src/app/(dashboard)/settings/page.tsx"): 1850,
    Path("web/src/app/(dashboard)/goals/page.tsx"): 1250,
    Path("web/src/app/(dashboard)/intel/page.tsx"): 1200,
}


def _imports_for(path: Path) -> list[str]:
    imports = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("from "):
            imports.append(stripped.split()[1])
        elif stripped.startswith("import "):
            modules = stripped[len("import ") :].split(",")
            imports.extend(part.strip().split()[0] for part in modules)
    return imports


def _python_files_under(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if p.name != "__init__.py"]


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def test_domains_do_not_import_surface_packages_directly():
    src_root = Path("src")
    offenders = []
    for domain in DOMAIN_ROOTS:
        for path in _python_files_under(src_root / domain):
            for imported in _imports_for(path):
                if imported.startswith(FORBIDDEN_DOMAIN_IMPORT_PREFIXES):
                    offenders.append(f"{path}: {imported}")
    assert offenders == []


def test_key_roots_have_local_readmes():
    missing = [
        str(root / "README.md") for root in DOCUMENTED_ROOTS if not (root / "README.md").exists()
    ]
    assert missing == []


def test_hotspot_files_stay_within_line_budget():
    offenders = []
    for path, budget in HOTSPOT_LINE_BUDGETS.items():
        actual = _line_count(path)
        if actual > budget:
            offenders.append(f"{path}: {actual} > {budget}")
    assert offenders == []


def test_surface_modules_do_not_import_other_surface_modules_directly():
    src_root = Path("src")
    offenders = []
    for surface in SURFACE_ROOTS:
        for path in _python_files_under(src_root / surface):
            current_surface = ".".join(path.relative_to(src_root).with_suffix("").parts[:2])
            for imported in _imports_for(path):
                if imported.startswith(
                    FORBIDDEN_SURFACE_IMPORT_PREFIXES
                ) and not imported.startswith(current_surface):
                    offenders.append(f"{path}: {imported}")
    assert offenders == []
