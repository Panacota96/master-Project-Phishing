# Workboard

This file is the source of truth for the deep-scan backlog, milestone layout, and branch naming policy.

## Operating Rules

- Confirmed defects become bug issues.
- Larger improvements stay grouped under milestone-backed initiative issues with implementation, docs, and validation child issues.
- Existing umbrella issues remain references only.
- Short-lived branches come from `main` using `fix/<issue-number>-<slug>`, `feature/<milestone-slug>`, `docs/<slug>`, or `chore/<slug>`.
- Open redirect tracking is deduplicated to open PR `#26`.

## Milestones

### Connectivity & Runtime Networking

- Milestone: [Connectivity & Runtime Networking](https://github.com/Panacota96/master-Project-Phishing/milestone/1)
- Parent issue: [#33](https://github.com/Panacota96/master-Project-Phishing/issues/33)
- Child issues: [#43](https://github.com/Panacota96/master-Project-Phishing/issues/43), [#44](https://github.com/Panacota96/master-Project-Phishing/issues/44), [#45](https://github.com/Panacota96/master-Project-Phishing/issues/45)
- Confirmed bugs: [#77](https://github.com/Panacota96/master-Project-Phishing/issues/77)
- Starter branch: `feature/connectivity-runtime-networking`
- Bug branch pattern: `fix/<issue-number>-networking`
- Status: Open

### Infrastructure Reliability & IaC Quality

- Milestone: [Infrastructure Reliability & IaC Quality](https://github.com/Panacota96/master-Project-Phishing/milestone/2)
- Parent issue: [#34](https://github.com/Panacota96/master-Project-Phishing/issues/34)
- Backlog:
  - [ ] [#46](https://github.com/Panacota96/master-Project-Phishing/issues/46) — implementation backlog and remediation slices
  - [ ] [#47](https://github.com/Panacota96/master-Project-Phishing/issues/47) — documentation and workboard synchronization
  - [ ] [#48](https://github.com/Panacota96/master-Project-Phishing/issues/48) — validation, smoke tests, and acceptance checks
- Confirmed bugs:
  - [ ] [#73](https://github.com/Panacota96/master-Project-Phishing/issues/73) — `terraform validate` fails in `elasticache.tf` (invalid `aws_default_vpc` data source)
- Starter branch: `feature/infrastructure-reliability-iac-quality`
- Bug branch pattern: `fix/<issue-number>-terraform`
- Status: Open (last sync: 2026-04-07)

### API Correctness & Contracts

- Milestone: [API Correctness & Contracts](https://github.com/Panacota96/master-Project-Phishing/milestone/3)
- Parent issue: [#35](https://github.com/Panacota96/master-Project-Phishing/issues/35)
- Child issues: [#49](https://github.com/Panacota96/master-Project-Phishing/issues/49), [#50](https://github.com/Panacota96/master-Project-Phishing/issues/50), [#51](https://github.com/Panacota96/master-Project-Phishing/issues/51)
- Confirmed bugs: [#78](https://github.com/Panacota96/master-Project-Phishing/issues/78)
- Starter branch: `feature/api-correctness-contracts`
- Bug branch pattern: `fix/<issue-number>-api`
- Status: Open

### Frontend UX & Accessibility

- Milestone: [Frontend UX & Accessibility](https://github.com/Panacota96/master-Project-Phishing/milestone/4)
- Parent issue: [#36](https://github.com/Panacota96/master-Project-Phishing/issues/36)
- Child issues: [#52](https://github.com/Panacota96/master-Project-Phishing/issues/52), [#53](https://github.com/Panacota96/master-Project-Phishing/issues/53), [#54](https://github.com/Panacota96/master-Project-Phishing/issues/54)
- Confirmed bugs: none yet
- Starter branch: `feature/frontend-ux-accessibility`
- Bug branch pattern: `fix/<issue-number>-frontend`
- Status: Open

### Backend Logic & Data Integrity

- Milestone: [Backend Logic & Data Integrity](https://github.com/Panacota96/master-Project-Phishing/milestone/10)
- Parent issue: [#37](https://github.com/Panacota96/master-Project-Phishing/issues/37)
- Child issues: [#55](https://github.com/Panacota96/master-Project-Phishing/issues/55), [#56](https://github.com/Panacota96/master-Project-Phishing/issues/56), [#57](https://github.com/Panacota96/master-Project-Phishing/issues/57)
- Confirmed bugs: [#76](https://github.com/Panacota96/master-Project-Phishing/issues/76)
- Starter branch: `feature/backend-logic-data-integrity`
- Bug branch pattern: `fix/<issue-number>-data`
- Status: Open

### Security, Identity & Session Hardening

- Milestone: [Security, Identity & Session Hardening](https://github.com/Panacota96/master-Project-Phishing/milestone/8)
- Parent issue: [#38](https://github.com/Panacota96/master-Project-Phishing/issues/38)
- Child issues: [#58](https://github.com/Panacota96/master-Project-Phishing/issues/58), [#59](https://github.com/Panacota96/master-Project-Phishing/issues/59), [#60](https://github.com/Panacota96/master-Project-Phishing/issues/60)
- Confirmed bugs: open redirect deduped to PR [#26](https://github.com/Panacota96/master-Project-Phishing/pull/26)
- Starter branch: `feature/security-identity-session-hardening`
- Bug branch pattern: `fix/<issue-number>-security`
- Status: Open

### DevOps & Local Developer Experience

- Milestone: [DevOps & Local Developer Experience](https://github.com/Panacota96/master-Project-Phishing/milestone/9)
- Parent issue: [#39](https://github.com/Panacota96/master-Project-Phishing/issues/39)
- Child issues: [#61](https://github.com/Panacota96/master-Project-Phishing/issues/61), [#62](https://github.com/Panacota96/master-Project-Phishing/issues/62), [#63](https://github.com/Panacota96/master-Project-Phishing/issues/63)
- Confirmed bugs: [#74](https://github.com/Panacota96/master-Project-Phishing/issues/74), [#75](https://github.com/Panacota96/master-Project-Phishing/issues/75)
- Starter branch: `feature/devops-local-developer-experience`
- Bug branch pattern: `fix/<issue-number>-local-dev`
- Status: Open

### Agentic Workflow & Repo Automation

- Milestone: [Agentic Workflow & Repo Automation](https://github.com/Panacota96/master-Project-Phishing/milestone/5)
- Parent issue: [#40](https://github.com/Panacota96/master-Project-Phishing/issues/40)
- Child issues: [#64](https://github.com/Panacota96/master-Project-Phishing/issues/64), [#65](https://github.com/Panacota96/master-Project-Phishing/issues/65), [#66](https://github.com/Panacota96/master-Project-Phishing/issues/66)
- Confirmed bugs: none yet
- Starter branch: `feature/agentic-workflow-repo-automation`
- Bug branch pattern: `fix/<issue-number>-automation`
- Status: Open

### CI/CD Quality Gates & Release Safety

- Milestone: [CI/CD Quality Gates & Release Safety](https://github.com/Panacota96/master-Project-Phishing/milestone/6)
- Parent issue: [#41](https://github.com/Panacota96/master-Project-Phishing/issues/41)
- Child issues: [#67](https://github.com/Panacota96/master-Project-Phishing/issues/67), [#68](https://github.com/Panacota96/master-Project-Phishing/issues/68), [#69](https://github.com/Panacota96/master-Project-Phishing/issues/69)
- Confirmed bugs: none yet
- Starter branch: `feature/cicd-quality-gates-release-safety`
- Bug branch pattern: `fix/<issue-number>-cicd`
- Status: Open

### Documentation & Architecture Visualization

- Milestone: [Documentation & Architecture Visualization](https://github.com/Panacota96/master-Project-Phishing/milestone/7)
- Parent issue: [#42](https://github.com/Panacota96/master-Project-Phishing/issues/42)
- Child issues: [#70](https://github.com/Panacota96/master-Project-Phishing/issues/70), [#71](https://github.com/Panacota96/master-Project-Phishing/issues/71), [#72](https://github.com/Panacota96/master-Project-Phishing/issues/72)
- Confirmed bugs: [#79](https://github.com/Panacota96/master-Project-Phishing/issues/79)
- Starter branch: `docs/workboard-and-architecture`
- Bug branch pattern: `docs/<slug>`
- Status: Open

## Validation Baseline

- `docker compose config`
- `terraform -chdir=phishing-platform-infra/terraform validate`
- `make docs-check`
- `make lint`
- `make test`

Track new validation notes in the relevant milestone issue and keep this file aligned with the GitHub backlog.
