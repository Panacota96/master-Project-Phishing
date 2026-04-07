from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
WORKBOARD = ROOT / "documentation" / "WORKBOARD.md"

STALE_PATTERNS = {
    "claude-code-review.yml": [
        ROOT / "README.md",
        ROOT / "CLAUDE.md",
        ROOT / "documentation",
    ],
    "Current version: **1.2.4**": [ROOT / "README.md"],
    "Current version (1.2.4)": [ROOT / "README.md"],
    "Copy `.env` (already present)": [ROOT / "CLAUDE.md"],
    "there is no public registration flow": [ROOT / "CLAUDE.md"],
    "**`dev`**: The default development branch.": [ROOT / "documentation" / "dev" / "CONTRIBUTING.md"],
    "up-to-date with `dev`": [ROOT / "documentation" / "dev" / "CONTRIBUTING.md"],
    "already present in the repo": [
        ROOT / "documentation" / "dev" / "SETUP.md",
        ROOT / "README.md",
    ],
}


def iter_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    allowed_suffixes = {".md", ".txt", ".yml", ".yaml", ".py"}
    return [
        path
        for path in target.rglob("*")
        if path.is_file() and path.suffix.lower() in allowed_suffixes
    ]


def main() -> int:
    errors: list[str] = []
    readme_text = README.read_text(encoding="utf-8")

    expected_badge = f"version-{VERSION}-blue"
    if expected_badge not in readme_text:
        errors.append(f"README badge is not aligned with VERSION={VERSION}.")

    expected_current_version = f"Current version: **{VERSION}**"
    if expected_current_version not in readme_text:
        errors.append("README current version line is not aligned with VERSION.")

    if not WORKBOARD.exists():
        errors.append("documentation/WORKBOARD.md is missing.")

    for pattern, targets in STALE_PATTERNS.items():
        for target in targets:
            for candidate in iter_files(target):
                text = candidate.read_text(encoding="utf-8")
                if pattern in text:
                    relative = candidate.relative_to(ROOT)
                    errors.append(f"Found stale pattern {pattern!r} in {relative}.")

    if errors:
        print("Documentation consistency checks failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Documentation consistency checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
