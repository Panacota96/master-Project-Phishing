from __future__ import annotations

import argparse
import os
from pathlib import Path

from scripts.github_automation_common import (
    GitHubRepoClient,
    STANDARD_LABEL_SPECS,
    WorkboardEntry,
    append_step_summary,
    author_can_write,
    load_event_payload,
    parse_issue_form_body,
    parse_issue_templates,
    parse_workboard,
    slugify,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKBOARD_PATH = PROJECT_ROOT / "documentation" / "WORKBOARD.md"
ISSUE_TEMPLATE_DIR = PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE"


def run_issue_intake(
    repo: GitHubRepoClient,
    event_name: str,
    payload: dict,
    *,
    workboard_path: Path = WORKBOARD_PATH,
    template_dir: Path = ISSUE_TEMPLATE_DIR,
) -> int:
    entries = parse_workboard(workboard_path)
    repo.ensure_labels(build_label_specs(entries))

    if event_name == "issue_comment":
        return handle_issue_comment_command(repo, payload)
    if event_name != "issues":
        append_step_summary("## Issue Intake\n\n- Unsupported event; nothing to do.\n")
        return 0

    issue = payload["issue"]
    issue_number = issue["number"]
    issue_body = issue.get("body", "")
    templates = parse_issue_templates(template_dir)
    template = match_template(issue["title"], templates)
    labels = {label["name"] for label in issue.get("labels", [])}
    changes: list[str] = []
    comments: list[str] = []

    if template:
        labels.update(template.default_labels)
        labels.add(template.type_label)
        changes.append(f"Applied type label `{template.type_label}`.")

    sections = parse_issue_form_body(issue_body)
    milestone_entry = None
    if template and template.type_label == "type:initiative":
        milestone_name = sections.get("Milestone", "").strip()
        milestone_entry = find_entry_by_title(entries, milestone_name)
        if milestone_entry:
            labels.add(milestone_entry.area_label)
            ensure_issue_milestone(repo, issue_number, issue, milestone_entry.milestone_number)
            changes.append(f"Assigned milestone `{milestone_entry.title}`.")
        else:
            labels.add("status:needs-workboard-sync")
            comments.append(
                f"Milestone `{milestone_name or '(missing)'}` is not present in `documentation/WORKBOARD.md`.\n\n"
                "Next step:\n"
                "1. Update `documentation/WORKBOARD.md` on `main`.\n"
                "2. Run `workboard-sync.yml` with `mode=apply`, or comment "
                "`/sync-workboard` after the workboard update lands."
            )
            changes.append("Flagged issue for workboard synchronization.")
    elif template and template.type_label in {"type:bug", "type:docs-debt", "type:security"}:
        milestone_entry = infer_milestone_from_issue(entries, issue["title"], issue_body)
        if milestone_entry:
            labels.add(milestone_entry.area_label)
            ensure_issue_milestone(repo, issue_number, issue, milestone_entry.milestone_number)
            changes.append(f"Inferred milestone `{milestone_entry.title}`.")
        else:
            labels.add("status:needs-triage")
            changes.append("Marked issue for maintainer triage.")

    repo.add_labels(issue_number, sorted(labels))
    for comment in comments:
        repo.create_comment(issue_number, comment)

    summary_lines = ["## Issue Intake", ""]
    summary_lines.extend(f"- {change}" for change in changes or ["No issue metadata changes required."])
    append_step_summary("\n".join(summary_lines) + "\n")
    return 0


def handle_issue_comment_command(repo: GitHubRepoClient, payload: dict) -> int:
    issue = payload.get("issue", {})
    if issue.get("pull_request"):
        return 0
    comment = (payload.get("comment") or {}).get("body", "").strip()
    author_association = (payload.get("comment") or {}).get("author_association", "")
    issue_number = issue.get("number")
    if comment != "/sync-workboard":
        return 0
    if not author_can_write(author_association):
        repo.create_comment(issue_number, "Only repository maintainers can run `/sync-workboard`.")
        return 1
    default_branch = repo.repo_default_branch()
    repo.dispatch_workflow("workboard-sync.yml", default_branch, {"mode": "apply"})
    repo.create_comment(
        issue_number,
        "Started `workboard-sync.yml` in `apply` mode against the default branch "
        "to reconcile GitHub state with `documentation/WORKBOARD.md`.",
    )
    append_step_summary("## Issue Intake\n\n- Dispatched `workboard-sync.yml` in `apply` mode.\n")
    return 0


def infer_milestone_from_issue(entries: list[WorkboardEntry], title: str, body: str) -> WorkboardEntry | None:
    haystack = f"{title}\n{body}".lower()
    exact_matches = [entry for entry in entries if entry.title.lower() in haystack]
    if len(exact_matches) == 1:
        return exact_matches[0]
    scored: list[tuple[int, WorkboardEntry]] = []
    for entry in entries:
        tokens = [token for token in slugify(entry.title).split("-") if len(token) > 2]
        score = sum(1 for token in tokens if token in haystack)
        if score >= 2:
            scored.append((score, entry))
    if not scored:
        return None
    scored.sort(key=lambda item: item[0], reverse=True)
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None
    return scored[0][1]


def ensure_issue_milestone(
    repo: GitHubRepoClient,
    issue_number: int,
    issue: dict,
    milestone_number: int | None,
) -> None:
    if milestone_number is None:
        return
    current = (issue.get("milestone") or {}).get("number")
    if current == milestone_number:
        return
    repo.update_issue(issue_number, milestone_number=milestone_number)


def match_template(title: str, templates: list) -> object | None:
    for template in templates:
        if title.startswith(template.title_prefix):
            return template
    return None


def find_entry_by_title(entries: list[WorkboardEntry], title: str) -> WorkboardEntry | None:
    normalized = title.strip().lower()
    for entry in entries:
        if entry.title.lower() == normalized:
            return entry
    return None


def build_label_specs(entries: list[WorkboardEntry]) -> dict[str, dict[str, str]]:
    specs = dict(STANDARD_LABEL_SPECS)
    for entry in entries:
        specs[entry.area_label] = {
            "color": "5319e7",
            "description": f"Work scoped to the '{entry.title}' milestone.",
        }
    return specs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize new issues into the milestone/workboard model.")
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", ""))
    parser.add_argument("--event-path", default=os.environ.get("GITHUB_EVENT_PATH"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.repository or not args.token:
        raise SystemExit("GITHUB_REPOSITORY and GITHUB_TOKEN are required.")
    payload = load_event_payload(args.event_path)
    repo = GitHubRepoClient(args.repository, args.token)
    return run_issue_intake(repo, args.event_name, payload)


if __name__ == "__main__":
    raise SystemExit(main())
