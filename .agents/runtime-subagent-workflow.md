# Runtime Sub-Agent Workflow

This document defines how iterative scans should run in this repository.

## Roles

- `triage-agent`: scans app code, tests, and docs for concrete bugs, regressions, and missing validations.
- `infra-agent`: scans Terraform, GitHub workflows, Docker, and deployment scripts for IaC, CI/CD, and runtime risks.
- `docs-agent`: scans README and `documentation/` for inconsistencies, stale guidance, and diagram improvements.
- `governance-agent`: converts confirmed findings into issues, milestones, sub-issues, branches, and policy tasks.

## Workflow

1. Baseline the repo state and record current branches, open issues, PRs, and workflow status.
2. Split the scan by domain and run the domain agents in parallel.
3. Deduplicate findings against existing issues, PRs, and documentation.
4. Open or update issues for confirmed bugs.
5. Create milestone-backed feature parents and sub-issues for larger improvements.
6. Sync the workboard and docs after each batch.
7. Apply branch and protection policy only after the backlog structure is stable.

## Handoff Rules

- A finding becomes a bug issue only when the code or configuration evidence is concrete.
- A promising improvement becomes a feature issue if it is useful but not a defect.
- Documentation-only mismatches stay in docs issues unless they also break runtime behavior.
- Existing umbrella issues are reference points, not the source of truth.

## Required Outputs Per Scan Batch

- Confirmed bug issues with a short root-cause note.
- Feature milestone or sub-issue updates for new capabilities.
- Workboard updates with status, branch name, and owner.
- A short validation note covering what was checked and what remains uncertain.
