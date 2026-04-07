from pathlib import Path

from scripts.github_automation_common import WorkboardEntry, parse_workboard
from scripts.workboard_sync import sync_workboard


class FakeRepo:
    def __init__(self, *, milestones=None, issues=None):
        self.milestones = list(milestones or [])
        self.issues = dict(issues or {})
        self.labels = {}
        self.created_milestones = []
        self.created_issues = []
        self.updated_issues = []

    def ensure_labels(self, label_specs):
        self.labels.update(label_specs)
        return list(label_specs)

    def list_milestones(self, state="all"):
        return list(self.milestones)

    def create_milestone(self, title, description):
        milestone = {"title": title, "description": description, "number": len(self.milestones) + 1}
        self.milestones.append(milestone)
        self.created_milestones.append(milestone)
        return milestone

    def get_issue(self, issue_number):
        return self.issues.get(issue_number)

    def create_issue(self, title, body, milestone_number=None, labels=None):
        number = max(self.issues or {0: None}) + 1
        issue = {
            "number": number,
            "title": title,
            "body": body,
            "milestone": {"number": milestone_number} if milestone_number is not None else None,
            "labels": [{"name": label} for label in labels or []],
        }
        self.issues[number] = issue
        self.created_issues.append(issue)
        return issue

    def update_issue(self, issue_number, milestone_number=None, **_kwargs):
        issue = self.issues[issue_number]
        issue["milestone"] = {"number": milestone_number}
        self.updated_issues.append((issue_number, milestone_number))
        return issue


def _write_workboard(tmp_path: Path) -> Path:
    path = tmp_path / "WORKBOARD.md"
    path.write_text(
        """
# Workboard

### Agentic Workflow & Repo Automation

- Milestone: [Agentic Workflow & Repo Automation](https://github.com/acme/repo/milestone/5)
- Parent issue: [#40](https://github.com/acme/repo/issues/40)
- Child issues: [#64](https://github.com/acme/repo/issues/64), [#65](https://github.com/acme/repo/issues/65), [#66](https://github.com/acme/repo/issues/66)
- Confirmed bugs: [#77](https://github.com/acme/repo/issues/77)
- Starter branch: `feature/agentic-workflow-repo-automation`
- Bug branch pattern: `fix/<issue-number>-automation`
- Status: Open
""".strip(),
        encoding="utf-8",
    )
    return path


def test_parse_workboard_current_shape():
    entries = parse_workboard(Path("documentation/WORKBOARD.md"))
    assert entries
    assert any(entry.title == "Agentic Workflow & Repo Automation" for entry in entries)


def test_sync_workboard_check_mode_detects_missing_items(tmp_path):
    workboard_path = _write_workboard(tmp_path)
    repo = FakeRepo()

    result = sync_workboard(repo, mode="check", workboard_path=workboard_path)

    assert result.drift
    assert any("Missing milestone" in item for item in result.drift)
    assert any("referenced initiative issue #40 is missing" in item for item in result.drift)


def test_sync_workboard_apply_mode_creates_missing_items(tmp_path):
    workboard_path = _write_workboard(tmp_path)
    repo = FakeRepo()

    result = sync_workboard(repo, mode="apply", workboard_path=workboard_path)

    assert repo.created_milestones
    assert repo.created_issues
    assert any("Milestone 'Agentic Workflow & Repo Automation'" in item for item in result.created)


def test_sync_workboard_apply_mode_updates_bug_milestone(tmp_path):
    workboard_path = _write_workboard(tmp_path)
    repo = FakeRepo(
        milestones=[{"title": "Agentic Workflow & Repo Automation", "number": 5}],
        issues={
            40: {"number": 40, "milestone": {"number": 5, "title": "Agentic Workflow & Repo Automation"}},
            64: {"number": 64, "milestone": {"number": 5, "title": "Agentic Workflow & Repo Automation"}},
            65: {"number": 65, "milestone": {"number": 5, "title": "Agentic Workflow & Repo Automation"}},
            66: {"number": 66, "milestone": {"number": 5, "title": "Agentic Workflow & Repo Automation"}},
            77: {"number": 77, "milestone": {"number": 1, "title": "Wrong Milestone"}},
        },
    )

    result = sync_workboard(repo, mode="apply", workboard_path=workboard_path)

    assert (77, 5) in repo.updated_issues
    assert any("Bug issue #77 milestone -> Agentic Workflow & Repo Automation" in item for item in result.updated)
