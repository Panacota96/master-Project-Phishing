# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
- Governance baseline for solo-safe development: `CODEOWNERS`, PR template, structured issue templates, a live workboard, and repo-local skills under `.agents/`.
- CI coverage for documentation drift and Terraform parsing via `docs-check` and `terraform-validate`.
- `code-review.yml` workflow to summarize PR review context against the required branch checks.

### Changed
- Local Docker defaults no longer rely on a pre-created `.env`; `.env.example` is now the explicit starting point.
- Documentation now treats `documentation/WORKBOARD.md` as the source of truth for milestone, issue, and branch tracking.
- Terraform, Docker, and config baselines were corrected to match the current repository layout and runtime behavior.

---

## [1.2.5] - 2026-04-04

### Added
- **Real-time cache + SSE**: provisioned ElastiCache Redis with pub/sub wiring in the dashboard for live stats and OpenPhish caching; added threat-cache DynamoDB table for TTL persistence.
- **Campaign mailer pipeline**: new SQS campaign queue, Lambda campaign mailer, EventBridge scheduler (optional), and DynamoDB `campaigns` + `campaign_events` tables for tracking.
- **Admin tooling**: dashboard now targets cohorts/groups for campaign launches and validation emails via SES with Redis-backed updates.
- **Build tooling**: `make campaign-mailer` + `scripts/build_campaign_mailer.sh` to package the new Lambda.

### Changed
- Main Lambda now runs inside the default VPC for Redis access and publishes campaign/threat feed updates through Redis where available.
- Local setup scripts and tests create the new DynamoDB tables and queues; README documents the additional env vars and targets.
- Split infrastructure assets into `phishing-platform-infra/` (Terraform, Ansible, legacy AWS helpers, infra scripts) and retargeted deploy workflows/docs to the new path.

---

## [1.2.4] - 2026-03-21

### Added

- **Full documentation overhaul** — accuracy and completeness pass across all 13 documentation files:
  - `documentation/operator/CICD.md` — full rewrite replacing GitLab CI content with accurate GitHub Actions coverage (4 workflows, OIDC auth flow, Mermaid pipeline diagram, required secrets/environments)
  - `documentation/dev/SETUP.md` — fixed all `en-garde-dev-*` table names to `phishing-app-dev-*`; added missing env vars (`DYNAMODB_COHORT_TOKENS`, `SQS_REGISTRATION_QUEUE_URL`, `SES_FROM_EMAIL`); added Docker Compose Option A section with `setup_local_db.py` step
  - `CLAUDE.md` — fixed `en-garde-dev-*` env var examples; added missing env vars; updated CI/CD deployment note to mention OIDC and all 4 workflows
  - `README.md` — fixed `en-garde-dev-*` table names and S3 bucket in Quick Start block
  - `documentation/ARCHITECTURE.md` — updated "En Garde" title to project name; fixed Lambda/IAM/S3/CloudWatch naming (`en-garde-*` → `phishing-app-*`); added new quizzes to quiz catalog; added AWS service badges; fixed local dev `.env` S3_BUCKET reference
  - `documentation/REQUIREMENTS.md` — updated title; added GDPR anonymous inspector requirement and QR+SQS registration requirement
  - `documentation/operator/DEPLOYMENT.md` — removed GitLab CI references; added GitHub Environment Setup section; fixed S3 bucket name examples
  - `documentation/operator/INFRASTRUCTURE.md` — added cohort-tokens table; fixed `en-garde` naming; added SQS DLQ; added AWS service badges
  - `documentation/operator/README.md` — replaced GitLab CI reference with GitHub Actions
  - `documentation/user/STUDENT_GUIDE.md` — replaced Obsidian image tags with descriptive text; added Quiz Completion and Inspector Completion sections
  - `documentation/user/ADMIN_GUIDE.md` — replaced Obsidian image tags with descriptive text; added QR Code Generation, Inspector Reset, and Answer Key Editor sections
  - `aws/README.md` — added deprecation banner (legacy EC2 guide)
- New developer guides: `documentation/dev/ADDING_QUIZZES.md` and `documentation/dev/ADDING_EML_FILES.md`

### Changed

- No application code changes in this release — documentation only.

---

## [1.2.3] - 2026-03-21

### Added

- **Documentation overhaul** — comprehensive update to all four documentation files based on a full codebase scan:
  - `documentation/ARCHITECTURE.md` — updated CI/CD pipeline diagram to reflect the actual three-job structure (`ci` → `plan_dev` → `deploy_dev`), IAM bootstrap step, `deploy-prod.yml` and `destroy.yml` workflows, and refined blueprint routing table with all current routes
  - `documentation/REQUIREMENTS.md` — added full functional requirements section (AUTH, QUIZ, INSP, DASH, WORK), expanded non-functional requirements, updated IAM permission tables to match current `github_actions_oidc.tf` (added `TagResource`, `UntagResource`, `ListTags` for Lambda; `GetFunctionCodeSigningConfig`; `ListIdentities` for SES; `GetSubscriptionAttributes`, `ListSubscriptionsByTopic` for SNS; `ListQueueTags` for SQS; `ListTagsForResource` for CloudWatch; `ListInstanceProfilesForRole`, `TagRole` for IAM), expanded DynamoDB and CloudWatch alarm reference tables
  - `CHANGELOG.md` — this entry

- **`VERSION` file** — added `VERSION` file at project root, set to `1.2.3`

### Changed

- No application code changes in this release — documentation only.

---

## [1.2.2] - 2026-03-21

### Added

- **Architecture documentation** (`documentation/ARCHITECTURE.md`) — 10 Mermaid diagrams rendered natively on GitHub covering:
  - System Overview (C4-style context: actors + all AWS services)
  - AWS Infrastructure (all resources grouped by service)
  - Flask Software Architecture (app factory, blueprints, models, config)
  - DynamoDB Schema (all 9 tables, PKs, SKs, GSIs, and relationships)
  - CI/CD Pipeline (push → CI → Terraform → seed full flow)
  - Login Flow (sequence diagram with auth paths)
  - Quiz Flow (flowchart including video gate and one-attempt enforcement)
  - Email Inspector Flow (sequence diagram with S3/DDB interactions per email)
  - QR Self-Registration Flow (async SQS/Lambda/SES registration sequence)
  - Local Development Architecture (Docker Compose vs standalone dev server)
- `README.md`: added link to `documentation/ARCHITECTURE.md` under the Requirements section

### Fixed

- **Makefile** (`S3_BUCKET := …` → `S3_BUCKET = …`): `S3_BUCKET` was a simply-expanded variable (`:=`), causing `terraform output` to run at **Makefile parse time** — before `terraform init` is called. This leaked a "Backend initialization required" Terraform error into the stderr of the `make lambda` CI step. Changed to a recursively-expanded variable (`=`) so the `terraform output` call only runs when `sync-assets` is actually invoked.
- **`deploy-dev.yml`**: Added `chmod +x scripts/*.sh` step before `make lambda`. Global `core.filemode=false` (set by Windows/WSL2 git config) can silently drop the execute bit when shell scripts are committed from a Windows filesystem, causing `Permission denied` on the runner despite the git tree recording `100755`. The explicit `chmod` makes the workflow resilient to this regardless of the committed file mode.

---

## [1.2.1] - 2026-03-21

### Added

- **UI overhaul** — quiz cards, score ring, stat cards, rank badges, and video gate redesign for improved student experience

### Fixed

- `fix: use direct S3 URL for videos` — CloudFront has no S3 origin configured; video assets must be served directly from S3
- `fix: update VIDEO_BASE_URL to use CloudFront URL for video assets` — seeder and README updated to reflect correct base URL
- `fix: app_name en-garde → phishing-app` — updated in all three workflow files (`deploy-dev.yml`, `deploy-prod.yml`, `destroy.yml`) so Terraform resource prefixes match the deployed infrastructure
- `fix: add CloudWatchLogDelivery IAM permission` — added `logs:CreateLogDelivery` and related permissions to `github_actions_oidc.tf` so API Gateway structured access logs can be configured by CI

---

## [1.2.0] - 2026-02-27

### Added

- **CloudFront distribution** (`terraform/cloudfront.tf`) — stable `dXXXXX.cloudfront.net` URL in front of API Gateway; survives Lambda/API Gateway destroy-recreate cycles without changing the URL shared with students
  - No custom domain or ACM certificate required (uses AWS-managed `*.cloudfront.net` certificate)
  - Zero-TTL caching — all requests pass through to the Flask app (correct for session-based app)
  - All cookies and query strings forwarded; all 7 HTTP methods allowed
  - HTTP → HTTPS redirect enforced via `viewer_protocol_policy = "redirect-to-https"`
- New Terraform output `cloudfront_url` in `terraform/outputs.tf` — prints the stable URL after `terraform apply`

---

## [1.2.0] - 2026-02-27

### Added

- **Editable Answer Key (Admin UI)** — admins can now change any email's classification (Phishing ↔ Spam) and required signals without a code deployment
  - New "Edit" button per row in **Admin → Inspector Analytics → View Answer Key & Troubleshoot**
  - Edit modal with classification radio buttons, signal checkboxes (all 10 signal types), and explanation textarea
  - "Save Changes" posts to `POST /dashboard/inspector/answer-key/edit`; row DOM is updated immediately without a page reload
  - "Reset to Default" posts to `POST /dashboard/inspector/answer-key/reset`; reverts to `answer_key.py` baseline
  - Yellow "overridden" badge shown on rows that have a DynamoDB override active
- **DynamoDB Answer Key Overrides table** (`DYNAMODB_ANSWER_KEY_OVERRIDES`) — persists admin overrides keyed by `email_file`; survives Lambda restarts
- **`get_effective_answer_key()`** in `app/models.py` — merges static `ANSWER_KEY` dict with DynamoDB overrides at runtime (overrides win); falls back gracefully if the table does not exist
- **`get_answer_key_overrides()`**, **`set_answer_key_override()`**, **`delete_answer_key_override()`** added to `app/models.py`
- **Dynamic signal count** — required signal count per email is now driven by `len(entry['signals'])` from the effective answer key, not hardcoded to 3
  - `api_email_detail` response includes `requiredSignals` (integer)
  - Student JS reads `requiredSignals` and updates instruction text ("Select exactly N phishing signal(s)") and submit validation accordingly
  - Server-side `api_submit` validates against the dynamic count
- New admin dashboard routes: `POST /dashboard/inspector/answer-key/edit` and `POST /dashboard/inspector/answer-key/reset`

### Changed

- `app/inspector/routes.py`: removed static `ANSWER_KEY` import; all answer key lookups now go through `get_effective_answer_key()`
- `app/dashboard/routes.py`: `inspector_answer_key()` passes `has_override` flag per item to template
- `app/templates/admin/inspector_answer_key.html`: column header renamed from "Required Phishing Signals (3)" → "Required Signals"
- README project description updated: "Cloud SecDevOps course (TP1/TP2)" → "Master Project"

### Fixed

- `tests/conftest.py`: added `DYNAMODB_ANSWER_KEY_OVERRIDES` env var (`test-answer-key-overrides`) and table creation so `get_effective_answer_key()` works correctly in tests

---

## [1.1.1] - 2026-02-18

### Fixed

- GitLab CI: corrected heredoc indentation in destroy jobs to prevent YAML/shell parse errors.
- GitLab CI: seed step now uses a venv to avoid PEP 668 "externally managed" failures.
- GitLab CI: seed step reads Terraform outputs from `terraform/` after `cd ..` to avoid invalid DynamoDB table names.
- Safe commit: `7f023ef3b34d6e6c1022a038e60fcae89dd8aee0`.

---

## [1.1.0] - 2026-02-12

### Added

- **Email Threat Inspector** (`/inspector/`) — a standalone email analysis tool modeled after TryHackMe's "Wareville Email Threat Inspector"
  - Sidebar listing all 6 `.eml` files from `examples/` with subject, from, to, and date metadata
  - Full email detail view with: message overview, HTML preview (sandboxed iframe), headers table, extracted links, attachments list, and security warnings
  - Client-side classification form: users classify each email as Spam or Phishing, select phishing signals, and receive immediate correct/incorrect feedback with CTF flags
  - 10 phishing signal categories supported: Impersonation, Typosquatting/Punycodes, External Sender Domain, Spoofing, Social Engineering Text, Sense of Urgency, Fake Invoice, Malicious Attachment, Fake Login Page, Side Channel Communication Attempt
  - Backend EML parsing using Python stdlib (`email` module) — no new dependencies
  - Path traversal protection on the email detail API endpoint
  - Security warnings auto-detected: From/Return-Path domain mismatch, punycode domains in links, suspicious `@` in URLs
- New Flask blueprint: `app/inspector/` with 3 routes (`/inspector/`, `/inspector/api/emails`, `/inspector/api/emails/<filename>`)
- Standalone dark-themed inspector template (does not extend `base.html`)
- "Email Inspector" link added to the main app navbar
- `.eml` files now included in Docker image (`COPY examples/ examples/` in Dockerfile, removed `examples/` from `.dockerignore`)

### Files Created

- `app/inspector/__init__.py` — Blueprint registration
- `app/inspector/routes.py` — API routes and EML parsing logic
- `app/templates/inspector/inspector.html` — Standalone inspector UI (CSS + JS)

### Files Modified

- `app/__init__.py` — Registered inspector blueprint
- `app/templates/base.html` — Added "Email Inspector" navbar link
- `.dockerignore` — Removed `examples/` exclusion
- `Dockerfile` — Added `COPY examples/ examples/`

---

## [1.0.0] - 2026-02-12

### Added

- **Phishing Awareness Quiz App** — Flask web application for phishing awareness training
  - User authentication: register, login, logout with password hashing (Werkzeug)
  - Admin vs regular user roles (`is_admin` flag)
  - Quiz system: list quizzes, take multiple-choice quizzes, view explanations after each question, progress bar, score summary with color-coded feedback
  - Quiz history per user
  - Admin dashboard: stat cards (total users, attempts, average score), score distribution bar chart (Chart.js), per-quiz stats table, recent activity table
  - Seed script (`seed.py`) creating admin user and 10 phishing awareness questions
- **Data models**: User, Quiz, Question, Answer, QuizAttempt (SQLAlchemy + SQLite)
- **Docker support**: Dockerfile (python:3.12-slim + gunicorn), docker-compose.yml (web + Nginx), Nginx reverse proxy config
- **AWS deployment guide**: `aws/README.md` with EC2 Free Tier setup, `user-data.sh` boot script, `env.example` template
- **Real phishing email samples** (`examples/`): 6 `.eml` files from TryHackMe Advent of Cyber lab covering fake invoices, impersonation, urgency, spoofing, punycode, and spam
- **TryHackMe reference materials** (`Phishing AOC/`): CTF flags/answers, download scripts, email inspector source HTML
