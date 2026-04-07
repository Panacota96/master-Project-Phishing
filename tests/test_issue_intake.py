from pathlib import Path

from scripts.issue_intake import run_issue_intake


class FakeRepo:
    def __init__(self):
        self.labels = {}
        self.added_labels = []
        self.updated_issues = []
        self.comments = []
        self.dispatched = []

    def ensure_labels(self, label_specs):
        self.labels.update(label_specs)
        return list(label_specs)

    def add_labels(self, issue_number, labels):
        self.added_labels.append((issue_number, labels))
        return labels

    def update_issue(self, issue_number, milestone_number=None, **_kwargs):
        self.updated_issues.append((issue_number, milestone_number))

    def create_comment(self, issue_number, body):
        self.comments.append((issue_number, body))

    def repo_default_branch(self):
        return "main"

    def dispatch_workflow(self, workflow_id, ref, inputs):
        self.dispatched.append((workflow_id, ref, inputs))


def _write_workboard(tmp_path: Path) -> Path:
    path = tmp_path / "WORKBOARD.md"
    path.write_text(
        """
# Workboard

### API Correctness & Contracts

- Milestone: [API Correctness & Contracts](https://github.com/acme/repo/milestone/3)
- Parent issue: [#35](https://github.com/acme/repo/issues/35)
- Child issues: [#49](https://github.com/acme/repo/issues/49), [#50](https://github.com/acme/repo/issues/50), [#51](https://github.com/acme/repo/issues/51)
- Confirmed bugs: [#78](https://github.com/acme/repo/issues/78)
- Starter branch: `feature/api-correctness-contracts`
- Bug branch pattern: `fix/<issue-number>-api`
- Status: Open
""".strip(),
        encoding="utf-8",
    )
    return path


def test_issue_intake_assigns_milestone_for_known_initiative(tmp_path):
    repo = FakeRepo()
    payload = {
        "issue": {
            "number": 101,
            "title": "[Initiative] API Correctness & Contracts",
            "body": "### Milestone\nAPI Correctness & Contracts\n\n### Objective\nTighten contracts",
            "labels": [],
            "milestone": None,
        }
    }

    code = run_issue_intake(repo, "issues", payload, workboard_path=_write_workboard(tmp_path))

    assert code == 0
    assert (101, 3) in repo.updated_issues
    labels = dict(repo.added_labels)[101]
    assert "type:initiative" in labels
    assert "area:api-correctness-contracts" in labels


def test_issue_intake_flags_unknown_initiative_milestone(tmp_path):
    repo = FakeRepo()
    payload = {
        "issue": {
            "number": 102,
            "title": "[Initiative] Unknown Milestone",
            "body": "### Milestone\nNot In Workboard\n\n### Objective\nTest",
            "labels": [],
            "milestone": None,
        }
    }

    run_issue_intake(repo, "issues", payload, workboard_path=_write_workboard(tmp_path))

    labels = dict(repo.added_labels)[102]
    assert "status:needs-workboard-sync" in labels
    assert repo.comments
    assert "workboard-sync.yml" in repo.comments[0][1]


def test_issue_intake_dispatches_sync_command_for_maintainer(tmp_path):
    repo = FakeRepo()
    payload = {
        "issue": {"number": 103},
        "comment": {"body": "/sync-workboard", "author_association": "OWNER"},
    }

    code = run_issue_intake(repo, "issue_comment", payload, workboard_path=_write_workboard(tmp_path))

    assert code == 0
    assert repo.dispatched == [("workboard-sync.yml", "main", {"mode": "apply"})]


def test_issue_intake_marks_bug_for_triage_when_no_match(tmp_path):
    repo = FakeRepo()
    payload = {
        "issue": {
            "number": 104,
            "title": "bug: unrelated defect",
            "body": "### Summary\nNothing here maps cleanly.\n",
            "labels": [],
            "milestone": None,
        }
    }

    run_issue_intake(repo, "issues", payload, workboard_path=_write_workboard(tmp_path))

    labels = dict(repo.added_labels)[104]
    assert "type:bug" in labels
    assert "status:needs-triage" in labels
