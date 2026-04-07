from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path

from scripts.github_automation_common import (
    GitHubRepoClient,
    STANDARD_CHILD_SUFFIXES,
    STANDARD_LABEL_SPECS,
    WorkboardEntry,
    append_step_summary,
    parse_workboard,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKBOARD_PATH = PROJECT_ROOT / "documentation" / "WORKBOARD.md"


@dataclass
class SyncResult:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    drift: list[str] = field(default_factory=list)

    def has_unresolved_drift(self) -> bool:
        return bool(self.drift)

    def to_markdown(self) -> str:
        lines = ["## Workboard Sync", ""]
        if self.created:
            lines.append("### Created")
            lines.extend(f"- {item}" for item in self.created)
            lines.append("")
        if self.updated:
            lines.append("### Updated")
            lines.extend(f"- {item}" for item in self.updated)
            lines.append("")
        if self.drift:
            lines.append("### Drift")
            lines.extend(f"- {item}" for item in self.drift)
            lines.append("")
        if not any((self.created, self.updated, self.drift)):
            lines.append("- No drift detected.")
        return "\n".join(lines).rstrip() + "\n"


def validate_branch_conventions(entry: WorkboardEntry) -> list[str]:
    errors: list[str] = []
    if "/" not in entry.starter_branch:
        errors.append(f"{entry.title}: starter branch '{entry.starter_branch}' is invalid.")
    if not (
        entry.starter_branch.startswith("feature/")
        or entry.starter_branch.startswith("docs/")
        or entry.starter_branch.startswith("chore/")
    ):
        errors.append(
            f"{entry.title}: starter branch '{entry.starter_branch}' must start with "
            "feature/, docs/, or chore/."
        )
    if "<issue-number>" not in entry.bug_branch_pattern and not entry.bug_branch_pattern.startswith("docs/"):
        errors.append(
            f"{entry.title}: bug branch pattern '{entry.bug_branch_pattern}' must include "
            "<issue-number> or use docs/<slug>."
        )
    return errors


def sync_workboard(repo: GitHubRepoClient, *, mode: str, workboard_path: Path = WORKBOARD_PATH) -> SyncResult:
    result = SyncResult()
    entries = parse_workboard(workboard_path)
    repo.ensure_labels(_build_label_specs(entries))
    milestones = {item["title"]: item for item in repo.list_milestones()}

    for entry in entries:
        result.drift.extend(validate_branch_conventions(entry))
        milestone = milestones.get(entry.title)
        if milestone is None:
            result.drift.append(f"Missing milestone '{entry.title}'.")
            if mode == "apply":
                milestone = repo.create_milestone(
                    entry.title,
                    f"Managed by documentation/WORKBOARD.md for {entry.title}.",
                )
                milestones[entry.title] = milestone
                result.created.append(f"Milestone '{entry.title}'")
        milestone_number = milestone["number"] if milestone and milestone.get("number") else None
        result.drift.extend(
            ensure_reference_issue(
                repo,
                entry=entry,
                issue_number=entry.parent_issue_number,
                milestone_number=milestone_number,
                mode=mode,
                result=result,
                kind="initiative",
            )
        )
        for index, issue_number in enumerate(
            entry.child_issue_numbers[: len(STANDARD_CHILD_SUFFIXES)]
        ):
            result.drift.extend(
                ensure_reference_issue(
                    repo,
                    entry=entry,
                    issue_number=issue_number,
                    milestone_number=milestone_number,
                    mode=mode,
                    result=result,
                    kind=f"child:{index}",
                )
            )
        for bug_issue_number in entry.bug_issue_numbers:
            issue = repo.get_issue(bug_issue_number)
            if issue is None:
                result.drift.append(
                    f"{entry.title}: bug issue #{bug_issue_number} is referenced in the workboard but missing from GitHub."
                )
                continue
            issue_milestone = (issue.get("milestone") or {}).get("title", "")
            if milestone and issue_milestone != milestone["title"]:
                result.drift.append(
                    f"{entry.title}: bug issue #{bug_issue_number} is assigned to milestone '{issue_milestone or 'none'}'."
                )
                if mode == "apply" and milestone_number is not None:
                    repo.update_issue(bug_issue_number, milestone_number=milestone_number)
                    result.updated.append(f"Bug issue #{bug_issue_number} milestone -> {entry.title}")

    append_step_summary(result.to_markdown())
    return result


def ensure_reference_issue(
    repo: GitHubRepoClient,
    *,
    entry: WorkboardEntry,
    issue_number: int | None,
    milestone_number: int | None,
    mode: str,
    result: SyncResult,
    kind: str,
) -> list[str]:
    if issue_number is None:
        return [f"{entry.title}: missing {kind} issue number in documentation/WORKBOARD.md."]
    issue = repo.get_issue(issue_number)
    if issue is None:
        message = f"{entry.title}: referenced {kind} issue #{issue_number} is missing."
        if mode != "apply":
            return [message]
        replacement = repo.create_issue(
            title=build_sync_issue_title(entry, kind),
            body=build_sync_issue_body(entry, kind),
            milestone_number=milestone_number,
            labels=build_sync_issue_labels(entry, kind),
        )
        replacement_number = replacement.get("number")
        result.created.append(
            f"Replacement {kind} issue #{replacement_number or 'dry-run'} for missing #{issue_number} ({entry.title})"
        )
        return [
            message,
            f"{entry.title}: update documentation/WORKBOARD.md to point to replacement "
            f"{kind} issue #{replacement_number or 'new issue'}."
        ]

    drift: list[str] = []
    issue_milestone = (issue.get("milestone") or {}).get("number")
    if milestone_number is not None and issue_milestone != milestone_number:
        drift.append(
            f"{entry.title}: {kind} issue #{issue_number} milestone is {(issue.get('milestone') or {}).get('title', 'none')}."
        )
        if mode == "apply":
            repo.update_issue(issue_number, milestone_number=milestone_number)
            result.updated.append(f"{kind} issue #{issue_number} milestone -> {entry.title}")
    return drift


def build_sync_issue_title(entry: WorkboardEntry, kind: str) -> str:
    if kind == "initiative":
        return f"[Initiative] {entry.title}"
    if kind == "child:0":
        return f"[{entry.title}] {STANDARD_CHILD_SUFFIXES[0]}"
    if kind == "child:1":
        return f"[{entry.title}] {STANDARD_CHILD_SUFFIXES[1]}"
    return f"[{entry.title}] {STANDARD_CHILD_SUFFIXES[2]}"


def build_sync_issue_body(entry: WorkboardEntry, kind: str) -> str:
    if kind == "initiative":
        return (
            "## Objective\n"
            f"Keep the '{entry.title}' milestone aligned with documentation/WORKBOARD.md.\n\n"
            "## Scope\n"
            "- Track implementation, docs, and validation slices under this milestone.\n"
            "- Keep GitHub issue state aligned with the canonical workboard.\n\n"
            "## Validation\n"
            "- Confirm documentation/WORKBOARD.md links remain current.\n"
            "- Confirm child issues and bug issues share the same milestone.\n"
        )
    suffix = STANDARD_CHILD_SUFFIXES[int(kind.split(":")[1])]
    return (
        f"Tracked under the **{entry.title}** milestone.\n\n"
        f"Expected child slice: {suffix}.\n\n"
        "Validation baseline:\n"
        "- `docker compose config`\n"
        "- `terraform -chdir=phishing-platform-infra/terraform validate`\n"
        "- `make docs-check`\n"
        "- `make lint`\n"
        "- `make test`\n"
    )


def build_sync_issue_labels(entry: WorkboardEntry, kind: str) -> list[str]:
    labels = [entry.area_label]
    if kind == "initiative":
        labels.append("type:initiative")
    elif kind == "child:1":
        labels.append("type:docs-debt")
    return labels


def _build_label_specs(entries: list[WorkboardEntry]) -> dict[str, dict[str, str]]:
    specs = dict(STANDARD_LABEL_SPECS)
    for entry in entries:
        specs[entry.area_label] = {
            "color": "5319e7",
            "description": f"Work scoped to the '{entry.title}' milestone.",
        }
    return specs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize GitHub milestones and issues from documentation/WORKBOARD.md."
    )
    parser.add_argument(
        "--mode",
        choices=("check", "apply"),
        default=os.environ.get("WORKBOARD_SYNC_MODE", "check"),
    )
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--workboard", default=str(WORKBOARD_PATH))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.repository or not args.token:
        raise SystemExit("GITHUB_REPOSITORY and GITHUB_TOKEN are required.")
    repo = GitHubRepoClient(args.repository, args.token, dry_run=args.mode == "check")
    result = sync_workboard(repo, mode=args.mode, workboard_path=Path(args.workboard))
    print(result.to_markdown())
    return 1 if result.has_unresolved_drift() else 0


if __name__ == "__main__":
    raise SystemExit(main())
