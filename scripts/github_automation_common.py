from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


AUTHOR_ASSOCIATION_WRITE = {"OWNER", "MEMBER", "COLLABORATOR"}

STANDARD_CHILD_SUFFIXES = (
    "Implementation backlog and remediation slices",
    "Documentation and workboard synchronization",
    "Validation, smoke tests, and acceptance checks",
)

STANDARD_LABEL_SPECS = {
    "type:bug": {"color": "d73a4a", "description": "Confirmed defects and behavior regressions."},
    "type:initiative": {"color": "0e8a16", "description": "Milestone-backed initiative tracking issue."},
    "type:docs-debt": {"color": "1d76db", "description": "Documentation cleanup or technical debt follow-up."},
    "type:security": {"color": "b60205", "description": "Security review, hardening, or threat-model work."},
    "status:needs-workboard-sync": {
        "color": "fbca04",
        "description": "GitHub backlog is not aligned with documentation/WORKBOARD.md.",
    },
    "status:needs-triage": {
        "color": "ededed",
        "description": "Needs maintainer milestone or area triage.",
    },
}


class GitHubRepoError(RuntimeError):
    """Raised when a GitHub API call fails."""


@dataclass
class IssueTemplate:
    path: Path
    name: str
    title_prefix: str
    default_labels: list[str]
    type_label: str


@dataclass
class WorkboardEntry:
    title: str
    milestone_number: int | None
    parent_issue_number: int | None
    child_issue_numbers: list[int]
    bug_issue_numbers: list[int]
    starter_branch: str
    bug_branch_pattern: str
    status: str

    @property
    def area_label(self) -> str:
        return f"area:{slugify(self.title)}"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def strip_wrapping_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def append_step_summary(text: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def parse_issue_templates(template_dir: Path) -> list[IssueTemplate]:
    mappings = {
        "bug_report.yml": "type:bug",
        "feature_initiative.yml": "type:initiative",
        "docs_or_debt.yml": "type:docs-debt",
        "security_review.yml": "type:security",
    }
    templates: list[IssueTemplate] = []
    for filename, type_label in mappings.items():
        path = template_dir / filename
        raw = path.read_text(encoding="utf-8")
        name_match = re.search(r"^name:\s*(.+)$", raw, re.MULTILINE)
        title_match = re.search(r"^title:\s*(.+)$", raw, re.MULTILINE)
        labels_match = re.search(r"^labels:\s*\n((?:\s+-\s+.+\n?)*)", raw, re.MULTILINE)
        labels: list[str] = []
        if labels_match:
            labels = [
                strip_wrapping_quotes(line.split("-", 1)[1].strip())
                for line in labels_match.group(1).splitlines()
                if line.strip().startswith("-")
            ]
        templates.append(
            IssueTemplate(
                path=path,
                name=strip_wrapping_quotes(name_match.group(1)) if name_match else path.stem,
                title_prefix=strip_wrapping_quotes(title_match.group(1)) if title_match else "",
                default_labels=labels,
                type_label=type_label,
            )
        )
    return templates


def parse_issue_form_body(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    if not body:
        return sections
    parts = re.split(r"^###\s+", body, flags=re.MULTILINE)
    for part in parts[1:]:
        lines = part.splitlines()
        if not lines:
            continue
        heading = lines[0].strip()
        content = "\n".join(lines[1:]).strip()
        sections[heading] = content
    return sections


def parse_codeowners(path: Path) -> list[str]:
    reviewers: list[str] = []
    if not path.exists():
        return reviewers
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        for owner in parts[1:]:
            if owner.startswith("@"):
                reviewers.append(owner[1:])
    unique_reviewers: list[str] = []
    for reviewer in reviewers:
        if reviewer not in unique_reviewers:
            unique_reviewers.append(reviewer)
    return unique_reviewers


def parse_workboard(path: Path) -> list[WorkboardEntry]:
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"^###\s+", text, flags=re.MULTILINE)
    entries: list[WorkboardEntry] = []
    for section in sections[1:]:
        lines = section.splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        body = "\n".join(lines[1:])

        milestone_number = _extract_first_int(body, r"/milestone/(\d+)")
        parent_issue_number = _extract_first_int(body, r"Parent issue:\s+\[#(\d+)\]")
        child_issue_numbers = _extract_issue_numbers(_extract_line(body, "Child issues"))
        bug_issue_numbers = _extract_issue_numbers(_extract_line(body, "Confirmed bugs"))
        starter_branch = _extract_value(body, "Starter branch")
        bug_branch_pattern = _extract_value(body, "Bug branch pattern")
        status = _extract_value(body, "Status")

        entries.append(
            WorkboardEntry(
                title=title,
                milestone_number=milestone_number,
                parent_issue_number=parent_issue_number,
                child_issue_numbers=child_issue_numbers,
                bug_issue_numbers=bug_issue_numbers,
                starter_branch=starter_branch,
                bug_branch_pattern=bug_branch_pattern,
                status=status,
            )
        )
    return entries


def _extract_line(body: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}:\s*(.+)$", body, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _extract_value(body: str, label: str) -> str:
    return _extract_line(body, label)


def _extract_first_int(body: str, pattern: str) -> int | None:
    match = re.search(pattern, body)
    return int(match.group(1)) if match else None


def _extract_issue_numbers(value: str) -> list[int]:
    if not value or "none yet" in value.lower():
        return []
    flattened: list[int] = []
    for match in re.findall(r"/issues/(\d+)|#(\d+)", value):
        if isinstance(match, tuple):
            for element in match:
                if element:
                    flattened.append(int(element))
            continue
        flattened.append(int(match))
    return flattened


def build_pr_body(template_path: Path, issue_number: int, issue_title: str, milestone_title: str) -> str:
    template = template_path.read_text(encoding="utf-8")
    template = re.sub(
        r"(## Summary\s*\n\s*)-",
        rf"\1- Implements #{issue_number}: {issue_title}",
        template,
        count=1,
        flags=re.MULTILINE,
    )
    template = re.sub(
        r"^- Issue:\s*$",
        f"- Issue: #{issue_number}",
        template,
        count=1,
        flags=re.MULTILINE,
    )
    template = re.sub(
        r"^- Milestone:\s*$",
        f"- Milestone: {milestone_title}",
        template,
        count=1,
        flags=re.MULTILINE,
    )
    return template


def extract_linked_issue_number(body: str) -> int | None:
    match = re.search(r"^- Issue:\s*(?:#|https://github\.com/.+/issues/)(\d+)\s*$", body, re.MULTILINE)
    return int(match.group(1)) if match else None


def extract_linked_milestone_title(body: str) -> str:
    match = re.search(r"^- Milestone:\s*(.+?)\s*$", body, re.MULTILINE)
    if not match:
        return ""
    return match.group(1).strip()


def validate_required_pr_fields(body: str) -> list[str]:
    errors: list[str] = []
    summary_match = re.search(r"## Summary\s*(.+?)\n## ", body, re.DOTALL)
    summary_block = summary_match.group(1).strip() if summary_match else ""
    summary_lines = [line.strip() for line in summary_block.splitlines() if line.strip()]
    if not summary_lines or all(
        line in {"-", "- Issue:", "- Milestone:"} for line in summary_lines
    ):
        errors.append("PR summary is blank.")
    if extract_linked_issue_number(body) is None:
        errors.append("Linked issue is missing from the PR template.")
    milestone_title = extract_linked_milestone_title(body)
    if not milestone_title or milestone_title == "-":
        errors.append("Linked milestone is missing from the PR template.")
    return errors


def validate_branch_name(branch_name: str, linked_issue_number: int | None, milestone_title: str) -> list[str]:
    errors: list[str] = []
    valid_pattern = re.compile(
        r"^(fix/\d+-[a-z0-9-]+|feature/[a-z0-9-]+|docs/[a-z0-9-]+|chore/[a-z0-9-]+)$"
    )
    if not valid_pattern.match(branch_name):
        errors.append(
            "Branch must match one of: fix/<issue-number>-<slug>, "
            "feature/<milestone-slug>, docs/<slug>, chore/<slug>."
        )
        return errors
    if branch_name.startswith("fix/") and linked_issue_number is not None:
        expected_prefix = f"fix/{linked_issue_number}-"
        if not branch_name.startswith(expected_prefix):
            errors.append(f"Bug-fix branch must start with {expected_prefix}.")
    if branch_name.startswith("feature/") and milestone_title:
        expected_slug = slugify(milestone_title)
        if branch_name != f"feature/{expected_slug}":
            errors.append(f"Feature branch must be feature/{expected_slug} for milestone '{milestone_title}'.")
    return errors


def author_can_write(author_association: str) -> bool:
    return author_association in AUTHOR_ASSOCIATION_WRITE


class GitHubRepoClient:
    def __init__(
        self,
        repository: str,
        token: str,
        *,
        api_url: str = "https://api.github.com",
        dry_run: bool = False,
    ) -> None:
        if "/" not in repository:
            raise ValueError(f"Invalid repository '{repository}'. Expected owner/repo.")
        self.repository = repository
        self.owner, self.repo = repository.split("/", 1)
        self.api_url = api_url.rstrip("/")
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        expected: tuple[int, ...] = (200,),
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.api_url}{path}"
        response = self.session.request(method, url, json=json_body, params=params, timeout=30)
        if response.status_code not in expected:
            raise GitHubRepoError(
                f"{method} {path} failed with {response.status_code}: {response.text}"
            )
        if response.status_code == 204 or not response.text:
            return None
        return response.json()

    def list_milestones(self, state: str = "all") -> list[dict[str, Any]]:
        return self.request(
            "GET",
            f"/repos/{self.repository}/milestones",
            expected=(200,),
            params={"state": state, "per_page": 100},
        )

    def create_milestone(self, title: str, description: str) -> dict[str, Any] | None:
        if self.dry_run:
            return {"title": title, "description": description, "number": None, "dry_run": True}
        return self.request(
            "POST",
            f"/repos/{self.repository}/milestones",
            expected=(201,),
            json_body={"title": title, "description": description},
        )

    def get_issue(self, issue_number: int) -> dict[str, Any] | None:
        try:
            return self.request(
                "GET",
                f"/repos/{self.repository}/issues/{issue_number}",
                expected=(200,),
            )
        except GitHubRepoError as exc:
            if "404" in str(exc):
                return None
            raise

    def create_issue(
        self,
        title: str,
        body: str,
        *,
        milestone_number: int | None = None,
        labels: list[str] | None = None,
    ) -> dict[str, Any] | None:
        if self.dry_run:
            return {
                "title": title,
                "body": body,
                "milestone": milestone_number,
                "labels": labels or [],
                "number": None,
                "dry_run": True,
            }
        payload: dict[str, Any] = {"title": title, "body": body}
        if milestone_number is not None:
            payload["milestone"] = milestone_number
        if labels:
            payload["labels"] = labels
        return self.request(
            "POST",
            f"/repos/{self.repository}/issues",
            expected=(201,),
            json_body=payload,
        )

    def update_issue(
        self,
        issue_number: int,
        *,
        milestone_number: int | None = None,
        labels: list[str] | None = None,
        body: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any] | None:
        if self.dry_run:
            return {
                "number": issue_number,
                "milestone": milestone_number,
                "labels": labels,
                "body": body,
                "title": title,
                "dry_run": True,
            }
        payload: dict[str, Any] = {}
        if milestone_number is not None:
            payload["milestone"] = milestone_number
        if labels is not None:
            payload["labels"] = labels
        if body is not None:
            payload["body"] = body
        if title is not None:
            payload["title"] = title
        return self.request(
            "PATCH",
            f"/repos/{self.repository}/issues/{issue_number}",
            expected=(200,),
            json_body=payload,
        )

    def add_labels(self, issue_number: int, labels: list[str]) -> list[dict[str, Any]] | None:
        if self.dry_run:
            return [{"name": label, "dry_run": True} for label in labels]
        return self.request(
            "POST",
            f"/repos/{self.repository}/issues/{issue_number}/labels",
            expected=(200,),
            json_body={"labels": labels},
        )

    def create_comment(self, issue_number: int, body: str) -> dict[str, Any] | None:
        if self.dry_run:
            return {"body": body, "issue_number": issue_number, "dry_run": True}
        return self.request(
            "POST",
            f"/repos/{self.repository}/issues/{issue_number}/comments",
            expected=(201,),
            json_body={"body": body},
        )

    def list_labels(self) -> list[dict[str, Any]]:
        return self.request(
            "GET",
            f"/repos/{self.repository}/labels",
            expected=(200,),
            params={"per_page": 100},
        )

    def create_label(self, name: str, color: str, description: str) -> dict[str, Any] | None:
        if self.dry_run:
            return {"name": name, "color": color, "description": description, "dry_run": True}
        return self.request(
            "POST",
            f"/repos/{self.repository}/labels",
            expected=(201,),
            json_body={"name": name, "color": color, "description": description},
        )

    def get_branch(self, branch_name: str) -> dict[str, Any] | None:
        encoded = requests.utils.quote(branch_name, safe="")
        try:
            return self.request(
                "GET",
                f"/repos/{self.repository}/branches/{encoded}",
                expected=(200,),
            )
        except GitHubRepoError as exc:
            if "404" in str(exc):
                return None
            raise

    def list_open_pulls_for_head(self, branch_name: str) -> list[dict[str, Any]]:
        return self.request(
            "GET",
            f"/repos/{self.repository}/pulls",
            expected=(200,),
            params={"state": "open", "head": f"{self.owner}:{branch_name}", "per_page": 100},
        )

    def create_pull(
        self,
        *,
        title: str,
        body: str,
        head: str,
        base: str,
        draft: bool,
    ) -> dict[str, Any] | None:
        if self.dry_run:
            return {"title": title, "body": body, "head": head, "base": base, "number": None, "dry_run": True}
        return self.request(
            "POST",
            f"/repos/{self.repository}/pulls",
            expected=(201,),
            json_body={"title": title, "body": body, "head": head, "base": base, "draft": draft},
        )

    def request_reviewers(self, pull_number: int, reviewers: list[str]) -> Any:
        if not reviewers:
            return None
        if self.dry_run:
            return {"pull_number": pull_number, "reviewers": reviewers, "dry_run": True}
        return self.request(
            "POST",
            f"/repos/{self.repository}/pulls/{pull_number}/requested_reviewers",
            expected=(201,),
            json_body={"reviewers": reviewers},
        )

    def get_pull(self, pull_number: int) -> dict[str, Any]:
        return self.request(
            "GET",
            f"/repos/{self.repository}/pulls/{pull_number}",
            expected=(200,),
        )

    def dispatch_workflow(self, workflow_id: str, ref: str, inputs: dict[str, str]) -> None:
        if self.dry_run:
            return
        self.request(
            "POST",
            f"/repos/{self.repository}/actions/workflows/{workflow_id}/dispatches",
            expected=(204,),
            json_body={"ref": ref, "inputs": inputs},
        )

    def repo_default_branch(self) -> str:
        repo = self.request("GET", f"/repos/{self.repository}", expected=(200,))
        return repo["default_branch"]

    def ensure_labels(self, label_specs: dict[str, dict[str, str]]) -> list[str]:
        existing = {label["name"] for label in self.list_labels()}
        created: list[str] = []
        for name, spec in label_specs.items():
            if name in existing:
                continue
            self.create_label(name, spec["color"], spec["description"])
            created.append(name)
        return created


def load_event_payload(path: str | None = None) -> dict[str, Any]:
    event_path = path or os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return {}
    with open(event_path, "r", encoding="utf-8") as handle:
        return json.load(handle)
