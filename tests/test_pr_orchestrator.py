from scripts.pr_orchestrator import run_pr_orchestrator


class FakeRepo:
    def __init__(self):
        self.issues = {
            12: {
                "number": 12,
                "title": "bug: API contract mismatch",
                "milestone": {"number": 3, "title": "API Correctness & Contracts"},
                "labels": [{"name": "type:bug"}, {"name": "area:api-correctness-contracts"}],
            }
        }
        self.branches = {"fix/12-api-contract-mismatch": {"name": "fix/12-api-contract-mismatch"}}
        self.open_pulls = []
        self.created_pulls = []
        self.updated_issues = []
        self.requested_reviewers = []
        self.comments = []
        self.pulls = {}

    def get_issue(self, issue_number):
        return self.issues.get(issue_number)

    def get_branch(self, branch_name):
        return self.branches.get(branch_name)

    def list_open_pulls_for_head(self, branch_name):
        return [pull for pull in self.open_pulls if pull["head"] == branch_name]

    def create_pull(self, **kwargs):
        pull = {"number": 44, "milestone": None, "head": {"ref": kwargs["head"]}, "body": kwargs["body"]}
        self.created_pulls.append(kwargs)
        self.pulls[44] = pull
        return pull

    def add_labels(self, issue_number, labels):
        self.updated_issues.append(("labels", issue_number, labels))

    def update_issue(self, issue_number, milestone_number=None, **_kwargs):
        self.updated_issues.append(("milestone", issue_number, milestone_number))

    def request_reviewers(self, pull_number, reviewers):
        self.requested_reviewers.append((pull_number, reviewers))

    def create_comment(self, issue_number, body):
        self.comments.append((issue_number, body))

    def get_pull(self, pull_number):
        return self.pulls[pull_number]


def test_pr_orchestrator_creates_draft_pull_request():
    repo = FakeRepo()
    payload = {
        "issue": {"number": 12},
        "comment": {"body": "/create-pr branch=fix/12-api-contract-mismatch", "author_association": "OWNER"},
    }

    code = run_pr_orchestrator(repo, "issue_comment", payload)

    assert code == 0
    assert repo.created_pulls
    assert ("milestone", 44, 3) in repo.updated_issues
    assert repo.comments[-1][1].startswith("Created draft PR #44")


def test_pr_orchestrator_rejects_duplicate_pull_request():
    repo = FakeRepo()
    repo.open_pulls.append({"head": "fix/12-api-contract-mismatch"})
    payload = {
        "issue": {"number": 12},
        "comment": {"body": "/create-pr branch=fix/12-api-contract-mismatch", "author_association": "OWNER"},
    }

    code = run_pr_orchestrator(repo, "issue_comment", payload)

    assert code == 1
    assert repo.comments
    assert "already exists" in repo.comments[-1][1]


def test_pr_orchestrator_validation_fails_on_branch_mismatch():
    repo = FakeRepo()
    repo.pulls[55] = {
        "number": 55,
        "body": "## Summary\n- Implements #12\n\n## Validation\n- [ ] x\n\n## Linked Work\n- Issue: #12\n- Milestone: API Correctness & Contracts\n\n## Deployment Notes\n- New environment variables:\n- Infra impact:\n- Docs updated:\n",
        "head": {"ref": "feature/wrong"},
        "milestone": {"title": "API Correctness & Contracts"},
    }
    payload = {"pull_request": {"number": 55}}

    code = run_pr_orchestrator(repo, "pull_request", payload)

    assert code == 1


def test_pr_orchestrator_skips_validation_for_agent_managed_branch():
    repo = FakeRepo()
    repo.pulls[56] = {
        "number": 56,
        "body": "",
        "head": {"ref": "copilot/review-project-structure-and-functionality"},
        "milestone": None,
    }
    payload = {"pull_request": {"number": 56}}

    code = run_pr_orchestrator(repo, "pull_request", payload)

    assert code == 0


def test_pr_orchestrator_rejects_unauthorized_comment():
    repo = FakeRepo()
    payload = {
        "issue": {"number": 12},
        "comment": {"body": "/create-pr branch=fix/12-api-contract-mismatch", "author_association": "CONTRIBUTOR"},
    }

    code = run_pr_orchestrator(repo, "issue_comment", payload)

    assert code == 1
    assert "Only repository maintainers" in repo.comments[-1][1]
