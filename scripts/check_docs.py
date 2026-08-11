from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
REQUIRED_SPEC_FILES = {"spec.md", "plan.md", "tasks.md"}
REQUIRED_GUIDES = {
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/architecture.md",
    "docs/catalog-integrations.md",
    "docs/cli-reference.md",
    "docs/configuration-reference.md",
    "docs/kimi-provider.md",
    "docs/lightroom-integration.md",
    "docs/recovery-and-review.md",
    "docs/troubleshooting.md",
    "packaging/README.md",
}


def tracked_markdown_files() -> list[Path]:
    skipped_parts = {".git", ".pytest_cache", ".venv", "venv", "env", "logs", "manifests", "rollback_reports"}
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if any(part in skipped_parts for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return sorted(files)


def check_links() -> list[str]:
    errors: list[str] = []
    for markdown_path in tracked_markdown_files():
        content = markdown_path.read_text(encoding="utf-8")
        for match in LINK_PATTERN.finditer(content):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("#"):
                continue
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            resolved = (markdown_path.parent / target_path).resolve(strict=False)
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(f"{markdown_path.relative_to(ROOT)} has link outside repo: {target}")
                continue
            if not resolved.exists():
                errors.append(f"{markdown_path.relative_to(ROOT)} has missing link: {target}")
    return errors


def check_specs() -> list[str]:
    errors: list[str] = []
    specs_root = ROOT / "specs"
    if not specs_root.exists():
        return ["specs/ directory is missing"]
    for spec_dir in sorted(path for path in specs_root.iterdir() if path.is_dir()):
        missing = [name for name in sorted(REQUIRED_SPEC_FILES) if not (spec_dir / name).exists()]
        if missing:
            errors.append(f"{spec_dir.relative_to(ROOT)} missing: {', '.join(missing)}")
    return errors


def check_required_guides() -> list[str]:
    return [f"Required guide is missing: {path}" for path in sorted(REQUIRED_GUIDES) if not (ROOT / path).exists()]


def check_cli_reference() -> list[str]:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_cli_reference.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return [] if result.returncode == 0 else [result.stdout.strip() or result.stderr.strip()]


def check_configuration_reference() -> list[str]:
    sys.path.insert(0, str(ROOT / "src"))
    from dataclasses import fields

    from photosage.config import PROVIDERS, AppConfig

    path = ROOT / "docs" / "configuration-reference.md"
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    errors = [
        f"Configuration reference missing AppConfig field: {field.name}" for field in fields(AppConfig) if f"`{field.name}`" not in content
    ]
    errors.extend(f"Configuration reference missing provider: {provider}" for provider in PROVIDERS if f"`{provider}`" not in content)
    return errors


def main() -> int:
    errors = check_links() + check_specs() + check_required_guides() + check_cli_reference() + check_configuration_reference()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Documentation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
