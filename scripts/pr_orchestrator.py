from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from scripts.github_automation_common import (
    GitHubRepoClient,
    append_step_summary,
    author_can_write,
    build_pr_body,
    extract_linked_issue_number,
    extract_linked_milestone_title,
    load_event_payload,
    parse_codeowners,
    validate_branch_name,
    validate_required_pr_fields,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PR_TEMPLATE_PATH = PROJECT_ROOT / ".github" / "pull_request_template.md"
CODEOWNERS_PATH = PROJECT_ROOT / ".github" / "CODEOWNERS"
AGENT_BRANCH_PREFIXES = ("copilot/", "codex/")


def run_pr_orchestrator(repo: GitHubRepoClient, event_name: str, payload: dict) -> int:
    if event_name == "pull_request":
        return validate_pull_request(repo, payload["pull_request"]["number"])
    if event_name == "workflow_dispatch":
        inputs = payload.get("inputs", {})
        issue_number = int(inputs["issue_number"])
        head_branch = inputs["head_branch"]
        base_branch = inputs.get("base_branch", "main")
        draft = str(inputs.get("draft", "true")).lower() == "true"
        return create_pull_request(repo, issue_number, head_branch, base_branch, draft)
    if event_name == "issue_comment":
        issue = payload.get("issue", {})
        comment = (payload.get("comment") or {}).get("body", "").strip()
        author_association = (payload.get("comment") or {}).get("author_association", "")
        if issue.get("pull_request"):
            return 0
        match = re.fullmatch(r"/create-pr\s+branch=(.+)", comment)
        if not match:
            return 0
        if not author_can_write(author_association):
            repo.create_comment(issue["number"], "Only repository maintainers can run `/create-pr`.")
            return 1
        return create_pull_request(repo, issue["number"], match.group(1).strip(), "main", True)
    append_step_summary("## PR Orchestrator\n\n- Unsupported event; nothing to do.\n")
    return 0


def create_pull_request(
    repo: GitHubRepoClient,
    issue_number: int,
    head_branch: str,
    base_branch: str,
    draft: bool,
) -> int:
    issue = repo.get_issue(issue_number)
    if issue is None:
        raise RuntimeError(f"Issue #{issue_number} does not exist.")
    if issue.get("pull_request"):
        raise RuntimeError(f"#{issue_number} is already a pull request, not an issue.")
    issue_milestone = issue.get("milestone") or {}
    milestone_title = issue_milestone.get("title", "").strip()
    if not milestone_title:
        repo.create_comment(
            issue_number,
            "Cannot create a PR until the issue has a milestone. Assign the correct milestone first.",
        )
        return 1
    branch = repo.get_branch(head_branch)
    if branch is None:
        repo.create_comment(
            issue_number,
            f"Cannot create a PR because branch `{head_branch}` does not exist remotely.",
        )
        return 1
    if repo.list_open_pulls_for_head(head_branch):
        repo.create_comment(
            issue_number,
            f"An open pull request already exists for branch `{head_branch}`.",
        )
        return 1
    branch_errors = validate_branch_name(head_branch, issue_number, milestone_title)
    if branch_errors:
        repo.create_comment(issue_number, "\n".join(f"- {error}" for error in branch_errors))
        return 1

    body = build_pr_body(PR_TEMPLATE_PATH, issue_number, issue["title"], milestone_title)
    pull = repo.create_pull(
        title=issue["title"],
        body=body,
        head=head_branch,
        base=base_branch,
        draft=draft,
    )
    pull_number = pull["number"]
    issue_labels = [label["name"] for label in issue.get("labels", [])]
    if issue_labels:
        repo.add_labels(pull_number, issue_labels)
    repo.update_issue(pull_number, milestone_number=issue_milestone.get("number"))
    reviewers = parse_codeowners(CODEOWNERS_PATH)
    repo.request_reviewers(pull_number, reviewers)
    repo.create_comment(
        issue_number,
        f"Created draft PR #{pull_number} for `{head_branch}` against `{base_branch}`.",
    )
    append_step_summary(
        "## PR Orchestrator\n\n"
        f"- Created draft PR #{pull_number} from `{head_branch}`.\n"
        f"- Linked issue: #{issue_number}\n"
        f"- Milestone: {milestone_title}\n"
    )
    return 0


def validate_pull_request(repo: GitHubRepoClient, pull_number: int) -> int:
    pull = repo.get_pull(pull_number)
    branch_name = pull["head"]["ref"]
    if branch_name.startswith(AGENT_BRANCH_PREFIXES):
        append_step_summary(
            "## PR Orchestrator Validation\n\n"
            f"- Skipped strict metadata validation for agent-managed branch `{branch_name}`.\n"
        )
        return 0

    body = pull.get("body") or ""
    errors = validate_required_pr_fields(body)
    linked_issue_number = extract_linked_issue_number(body)
    linked_milestone = extract_linked_milestone_title(body)

    if linked_issue_number is None:
        errors.append("Unable to validate milestone consistency because the linked issue is missing.")
    else:
        issue = repo.get_issue(linked_issue_number)
        if issue is None:
            errors.append(f"Linked issue #{linked_issue_number} does not exist.")
        else:
            issue_milestone = (issue.get("milestone") or {}).get("title", "")
            pr_milestone = (pull.get("milestone") or {}).get("title", "")
            if issue_milestone != pr_milestone:
                errors.append(
                    f"PR milestone '{pr_milestone or 'none'}' does not match linked issue "
                    f"milestone '{issue_milestone or 'none'}'."
                )
            if linked_milestone and linked_milestone != issue_milestone:
                errors.append(
                    f"PR template milestone '{linked_milestone}' does not match linked issue "
                    f"milestone '{issue_milestone or 'none'}'."
                )
            errors.extend(validate_branch_name(branch_name, linked_issue_number, issue_milestone))

    summary = ["## PR Orchestrator Validation", ""]
    if errors:
        summary.append("### Errors")
        summary.extend(f"- {error}" for error in errors)
        append_step_summary("\n".join(summary) + "\n")
        return 1
    summary.append("- PR metadata and branch naming passed validation.")
    append_step_summary("\n".join(summary) + "\n")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or validate pull requests from issue context.")
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
    return run_pr_orchestrator(repo, args.event_name, payload)


if __name__ == "__main__":
    raise SystemExit(main())
