"""Architecture guardrail tests for package dependency boundaries."""

from pathlib import Path

FORBIDDEN_DOMAIN_IMPORT_PREFIXES = ("cli.", "web.")
DOMAIN_ROOTS = ("advisor", "intelligence", "research", "services")
SURFACE_ROOTS = ("web/routes", "cli/commands", "coach_mcp/tools")
FORBIDDEN_SURFACE_IMPORT_PREFIXES = ("web.routes", "cli.commands", "coach_mcp.tools")


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


def test_domains_do_not_import_surface_packages_directly():
    src_root = Path("src")
    offenders = []
    for domain in DOMAIN_ROOTS:
        for path in _python_files_under(src_root / domain):
            for imported in _imports_for(path):
                if imported.startswith(FORBIDDEN_DOMAIN_IMPORT_PREFIXES):
                    offenders.append(f"{path}: {imported}")
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
