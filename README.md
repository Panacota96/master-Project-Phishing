<p align="center">
  <img src="app/static/images/en_garde_logo.png" width="180" alt="EnGarde Logo" />
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="app/static/images/esme_logo.png" width="100" alt="ESME Logo" />
</p>

<h1 align="center">EnGarde — Phishing Awareness Training</h1>

<p align="center">
  An interactive phishing awareness platform for engineering students — quizzes, video training, and a hands-on Email Threat Inspector, all running serverless on AWS.
</p>

<p align="center">
  Built to make phishing defense practical, measurable, and easier to teach.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.2.5-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-3.1.0-000000?style=flat-square&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/Terraform-%3E%3D1.5-7B42BC?style=flat-square&logo=terraform&logoColor=white" />
  <img src="https://img.shields.io/badge/AWS_Lambda-FF9900?style=flat-square&logo=awslambda&logoColor=white" />
  <img src="https://img.shields.io/badge/License-CC0-lightgrey?style=flat-square" />
</p>

<p align="center">
  <a href="https://buymeacoffee.com/santiagogow">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee" />
  </a>
</p>

> Why it matters: this repo shows how I translate blue-team awareness into hands-on student training with real phishing signals, analytics, and deployable infrastructure.

---

## Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Email Sample Library](#email-sample-library)
- [DynamoDB Schema](#dynamodb-schema)
- [Quick Start (Local)](#quick-start-local)
- [Docker Compose](#docker-compose-recommended-for-local-dev)
- [Make Targets](#make-targets)
- [CI/CD Overview](#cicd-overview)
- [AWS Deployment](#aws-deployment)
- [Documentation Index](#documentation-index)
- [Workboard](#workboard)
- [Admin Operations](#admin-operations-guide)
- [Improving Example Emails](#improving-example-emails-realism-checklist)
- [Contributing](#contributing)
- [Changelog & License](#changelog--license)

---

## About the Project

**EnGarde** (formerly *Master-Project-Phishing*) is a full-stack phishing awareness training application built for the [ESME](https://www.esme.fr/) engineering school master's programme. The name is a fencing call — *en garde*, be on guard — matching the project's mission: training students to recognize and defend against phishing attacks before they become real victims.

The platform consists of two complementary training tools:

| Tool | Description |
|---|---|
| **Phishing Quiz** | Multiple-choice quizzes gated behind video lessons. Students watch a training video, then answer questions testing recognition of real phishing techniques. |
| **Email Threat Inspector** | A sandboxed email viewer that presents real `.eml` phishing and spam samples. Students classify each email and identify the phishing signals it contains. |

Results from both tools are tracked per student and per cohort, giving instructors actionable analytics through an admin dashboard.

### The 10 Phishing Signal Categories

Every phishing email in the inspector is annotated with one or more of these signals:

| Signal | Key | Description |
|---|---|---|
| Impersonation | `impersonation` | Sender pretends to be a known person or brand |
| Typosquatting / Punycode | `punycode` | Look-alike domain using homograph or typo tricks |
| External Sender Domain | `externaldomain` | Email comes from a domain unrelated to the claimed sender |
| Spoofing | `spoof` | Display name or header crafted to deceive |
| Social Engineering | `socialeng` | Psychological manipulation (authority, fear, curiosity) |
| Urgency | `urgency` | Artificial time pressure to bypass critical thinking |
| Fake Invoice | `fakeinvoice` | Fraudulent billing or payment request |
| Malicious Attachment | `attachment` | Dangerous file disguised as legitimate document |
| Fake Login Page | `fakelogin` | Link leads to a credential-harvesting page |
| Side Channel Communication | `sidechannel` | Uses QR codes, phone numbers, or other out-of-band vectors |

---

## Features

### Phishing Quiz
- Multiple-choice quizzes covering URL analysis, spoofing, urgency tactics, CEO fraud, smishing, MFA bypass, and more
- Detailed explanations after each question showing why an answer is correct
- Progress bar, color-coded score summary, rank badge, and full quiz history per user
- Each quiz requires watching a training video before it unlocks
- Quizzes are defined in DynamoDB and seeded via `seed_dynamodb.py` — no code change needed to add new quizzes

### Email Threat Inspector
- Standalone tool at `/inspector/` for hands-on analysis of real `.eml` files stored in S3
- Renders: message overview, full headers, sandboxed HTML preview, extracted links, attachment list, and security warnings
- Users classify each email as **Spam** or **Phishing** and select the exact signals that give it away
- Per-session pool of up to 8 emails (1–3 spam + phishing) drawn randomly from the S3 bucket
- Required signal count per email is dynamic — driven by the answer key, never hardcoded
- Submissions are saved to a GDPR-safe anonymous table (no username stored)
- Session locked after all 8 emails are submitted; admin can reset individually or by cohort

### Admin Dashboard
- Stats overview: total users, total quiz attempts, average score, score distribution chart
- Per-quiz statistics, cohort analytics, and inspector signal accuracy reporting
- Real-time stats polling and OpenPhish live threat feed widget
- Redis/ElastiCache pub/sub for live SSE dashboard updates and SQS-backed campaign launcher (Lambda mailer + SES) with optional EventBridge scheduling
- **Risk Dashboard**: per-cohort risk score combining quiz failure rate and inspector signal miss rate
- CSV report generation with pre-signed S3 download links
- **Answer Key Editor**: change any email's classification and signals without a code deployment — overrides stored in DynamoDB take precedence over the static `answer_key.py` at runtime

### Authentication & User Management
- Login / Logout with form validation and Werkzeug password hashing
- Roles via `role` field (`admin`, `instructor`, `student`) — admin + instructor share dashboard access; mapped from Microsoft 365 groups when SSO is enabled
- Public `/auth/register` currently exists for QR-assisted onboarding; token enforcement hardening is tracked in issue `#78`
- Bulk student import via CSV upload
- QR code generation for cohort self-registration: students scan → fill form → Lambda worker creates account + sends SES confirmation email
- Students can change their own password

---

## Tech Stack

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-3.1.0-000000?style=flat-square&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/Bootstrap-5-7952B3?style=flat-square&logo=bootstrap&logoColor=white" />
  <img src="https://img.shields.io/badge/Chart.js-FF6384?style=flat-square&logo=chartdotjs&logoColor=white" />
  <br/>
  <img src="https://img.shields.io/badge/AWS_Lambda-FF9900?style=flat-square&logo=awslambda&logoColor=white" />
  <img src="https://img.shields.io/badge/DynamoDB-4053D6?style=flat-square&logo=amazondynamodb&logoColor=white" />
  <img src="https://img.shields.io/badge/Amazon_S3-569A31?style=flat-square&logo=amazons3&logoColor=white" />
  <img src="https://img.shields.io/badge/Amazon_SQS-FF4F8B?style=flat-square&logo=amazonsqs&logoColor=white" />
  <img src="https://img.shields.io/badge/ElastiCache_Redis-C925D1?style=flat-square&logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/EventBridge-8A2BE2?style=flat-square&logo=amazonaws&logoColor=white" />
  <img src="https://img.shields.io/badge/Amazon_SES-232F3E?style=flat-square&logo=amazonaws&logoColor=white" />
  <img src="https://img.shields.io/badge/CloudFront-232F3E?style=flat-square&logo=amazonaws&logoColor=white" />
  <img src="https://img.shields.io/badge/API_Gateway-FF4F8B?style=flat-square&logo=amazonaws&logoColor=white" />
  <img src="https://img.shields.io/badge/CloudWatch-FF4F8B?style=flat-square&logo=amazonaws&logoColor=white" />
  <br/>
  <img src="https://img.shields.io/badge/Terraform-%3E%3D1.5-7B42BC?style=flat-square&logo=terraform&logoColor=white" />
  <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Nginx-009639?style=flat-square&logo=nginx&logoColor=white" />
</p>

| Component | Technology |
|-----------|-----------|
| Backend | Flask 3.1 (Python 3.12), Flask-Login, Flask-WTF, Werkzeug |
| Database | AWS DynamoDB — 9 on-demand tables |
| Frontend | Jinja2 + Bootstrap 5 (CDN), Chart.js |
| EML Parsing | Python `email` stdlib (zero extra dependencies) |
| QR Codes | qrcode[pil] 8.0 |
| Lambda Adapter | Mangum 0.19 (ASGI wrapper for AWS Lambda) |
| WSGI Server | Gunicorn 23 (local / Docker) |
| Async Workers | AWS SQS + Lambda (registration worker) |
| Email | AWS SES |
| Tracing | AWS X-Ray SDK |
| Deployment | AWS Lambda + API Gateway v2 + CloudFront + Terraform |
| CI/CD | GitHub Actions (OIDC — no static AWS keys) |

**Requirements:** Python 3.12 · Terraform >= 1.5 · AWS CLI v2 · Docker + Compose. See [`documentation/REQUIREMENTS.md`](documentation/REQUIREMENTS.md) for the full IAM permissions list and [`documentation/ARCHITECTURE.md`](documentation/ARCHITECTURE.md) for 10 detailed Mermaid architecture diagrams.

---

## Repository Structure

The repository is organised as a monorepo with a clear boundary between the **Flask application** and the **AWS infrastructure**. See [`documentation/REPO_SEPARATION.md`](documentation/REPO_SEPARATION.md) for a guide to splitting these into two standalone repositories.

```
master-Project-Phishing/
├── app/                              # Flask application (blueprints, models, templates, static)
├── tests/                            # Pytest test suite
├── scripts/                          # Build, content, and utility scripts
├── documentation/                    # Full documentation suite
│   ├── dev/                          # Developer guides (setup, contributing, testing, EML)
│   ├── operator/                     # Operations guides (deployment, infra, CI/CD)
│   ├── user/                         # End-user guides (student, admin)
│   ├── ARCHITECTURE.md               # System design + Mermaid diagrams
│   └── REPO_SEPARATION.md            # Guide to splitting app vs infra into separate repos
├── examples/                         # Real-world .eml phishing samples
├── nginx/                            # Nginx reverse proxy configuration
├── phishing-platform-infra/          # AWS infrastructure (Terraform, Lambda source, scripts)
│   ├── terraform/                    # Infrastructure as Code (Lambda, DDB, S3, CloudFront…)
│   ├── lambda/                       # Lambda function source code
│   │   ├── campaign_mailer/          # Campaign mailer Lambda (SQS → SES)
│   │   └── registration_worker/      # Registration worker Lambda (SQS → DDB → SES)
│   ├── ansible/                      # Optional VM deployment playbooks
│   ├── aws/                          # Legacy EC2 deployment guide (deprecated)
│   └── scripts/                      # Infra + migration helper scripts
├── .github/workflows/                # GitHub Actions CI/CD
├── jury-presentation/                # Project review presentation materials
├── phishing-aoc/                     # TryHackMe Advent of Cyber reference materials
├── Dockerfile                        # Python 3.12-slim + Gunicorn
├── docker-compose.yml                # Web + Nginx + DynamoDB Local dev stack
├── seed_dynamodb.py                  # Seeds admin user + quizzes
├── setup_local_db.py                 # Creates all DynamoDB tables locally
├── config.py                         # Env var → app config mapping
├── run.py                            # Local development entry point
├── requirements.txt                  # Python runtime dependencies
├── Makefile                          # Build and workflow shortcuts
├── VERSION                           # Current version
└── CHANGELOG.md                      # Version history
```

---

### `app/` — Flask Application

The Flask app is created by `app/__init__.py` via the `create_app()` factory. It initialises `boto3` clients for DynamoDB, S3, and SQS on the app object, then registers four blueprints:

| Blueprint | URL Prefix | Responsibility |
|-----------|-----------|----------------|
| `app/auth/` | `/auth` | Login, logout, password change, QR self-registration, CSV bulk import |
| `app/quiz/` | `/quiz` | Quiz list, video gate, take quiz, finish/results, history |
| `app/dashboard/` | `/dashboard` | Admin stats, cohort analytics, risk dashboard, CSV reports, answer key editor, bug reports |
| `app/inspector/` | `/inspector` | Email Threat Inspector — EML list, detail view, submit answers (JSON API) |

Key files:

| File | Purpose |
|---|---|
| `app/models.py` | **Single data access layer** — all DynamoDB reads/writes. Never call `boto3` directly from routes. |
| `app/inspector/answer_key.py` | Static ground-truth baseline: classification (`Phishing`/`Spam`) + required signals per email file |
| `app/templates/` | Jinja2 templates organised by blueprint (`base.html`, `auth/`, `quiz/`, `dashboard/`, `inspector/`) |
| `app/static/` | CSS, JS, SVG icons, brand logos, training videos (videos gitignored — hosted in S3) |
| `app/static/images/en_garde_logo.png` | EnGarde project logo |
| `app/static/images/esme_logo.png` | ESME school logo |
| `app/static/images/logos/` | 11 SVG brand logos used in phishing training emails |

---

### `tests/` — Test Suite

pytest-based tests with full AWS mocking via `moto`. No real AWS account needed.

- `conftest.py` — `mock_aws()` fixture creates all 9 DynamoDB tables + S3 bucket; exposes `seed_admin`, `seed_user`, `seed_quiz` fixtures and a `login()` helper
- CSRF is disabled in test mode
- Run: `make test` (outputs JUnit XML report)
- Lint: `make lint` (flake8, max-line-length=120)

> **Note:** Most tests should keep using the `seed_user` fixture instead of driving `/auth/register`; registration hardening is tracked separately in issue `#78`.

---

### `phishing-platform-infra/` — Infrastructure Repository

Infrastructure is now isolated under `phishing-platform-infra/` so it can be pushed to a dedicated `phishing-platform-infra` repo. Run all Terraform commands from `phishing-platform-infra/terraform`.

| Path | Purpose |
|---|---|
| `terraform/` | AWS IaC (Lambda, API Gateway, DynamoDB, S3, CloudFront, IAM, SQS, SNS, CloudWatch) |
| `ansible/` | Optional VM provisioning playbooks (alternative to Lambda) |
| `aws/` | Legacy EC2 user-data scripts and AMI notes |
| `scripts/` | Infra + migration helpers (`import_resources.sh`, `migrate_dynamodb.py`, `migrate_inspector_attempts.py`, `migrate_s3.sh`) |
| `terraform.tfstate` | Local state snapshot (move to remote state before real deploys) |

**Terraform module index (`phishing-platform-infra/terraform/`):**

| File | AWS Services |
|---|---|
| `lambda.tf` | Flask app Lambda (Python 3.12, 512 MB, 30 s timeout) |
| `lambda_registration_worker.tf` | Registration worker Lambda (256 MB) |
| `api_gateway.tf` | HTTP API v2 — catch-all `$default` → Lambda proxy |
| `cloudfront.tf` | CloudFront distribution — stable URL over API Gateway |
| `dynamodb.tf` | 9 on-demand DynamoDB tables with GSIs |
| `s3.tf` | S3 bucket for EML samples + training videos |
| `sqs_registration.tf` | SQS queue + dead-letter queue for registrations |
| `sns_ses_registration.tf` | SNS topic + SES identity for confirmation emails |
| `cloudwatch_monitoring.tf` | Alarms, dashboard, X-Ray tracing |
| `iam.tf` | Lambda execution roles + GitHub Actions OIDC deploy role |
| `acm_custom_domain.tf` | ACM certificate + Route 53 DNS validation (optional) |
| `github_actions_oidc.tf` | Federated identity for CI/CD (no static keys) |
| `bootstrap/` | One-time setup: creates the S3 Terraform state bucket |
| `backend/dev.hcl` · `backend/prod.hcl` | Remote state configuration per environment |

**Environments:** `dev` (auto-deploys on push to `main`) and `prod` (manual dispatch). Both use OIDC — no AWS keys stored in GitHub.

---

### `documentation/` — Full Documentation Suite

23 documents organised by audience. See the [Documentation Index](#documentation-index) section below for the full table with links.

```
documentation/
├── ARCHITECTURE.md          # 10 Mermaid diagrams: system overview, AWS infra,
│                            # DynamoDB schema, CI/CD, all major flows
├── REQUIREMENTS.md          # Infrastructure, functional & IAM requirements
├── AUDIT_AND_ROADMAP.md     # Audit findings + feature roadmap
├── AWS_IMPROVEMENTS.md      # AWS cost and architecture optimisation proposals
├── COMPLIANCE_FRAMEWORKS.md # Compliance framework overview
├── GDPR_COMPLIANCE.md       # GDPR notes (anonymous inspector table, data retention)
├── FEATURE_PROPOSALS.md     # Future feature ideas
├── dev/                     # Developer guides (setup, contributing, adding content)
├── operator/                # Operator guides (deployment, infrastructure, CI/CD, maintenance)
└── user/                    # User guides (student handbook, admin guide)
```

---

### `examples/` — Phishing Email Sample Library

98 real-world style `.eml` files used in the Email Threat Inspector, organised by attack category. All files are synced to S3 under the `eml-samples/` prefix.

```
examples/
├── fake-invoice/            # PayPal, Microsoft, FedEx, Apple invoice fraud
├── impersonation/           # Voice messages, SharePoint, Zoom, IT Helpdesk, callback phishing
├── impersonation-urgency/   # Impersonation + urgency combinations
├── legit-impersonation/     # Convincing legitimate-looking impersonation
├── punycode/                # Homograph attacks, typosquatting, subdomain deception
├── realistic_templates/     # High-fidelity spam and phishing templates
├── spam/                    # Marketing, logistics, newsletter, coupon, QR, survey
├── linksec/                 # Cloud service impersonation (15 platforms — see below)
│   ├── amazon-web-services-aws/
│   ├── bluejeans/
│   ├── cisco/
│   ├── google-cloud-platform-gcp/
│   ├── google-workspace/
│   ├── gotomeeting/
│   ├── ibm-cloud/
│   ├── microsoft-azure/
│   ├── microsoft-office-365/
│   ├── microsoft-teams/
│   ├── oracle-cloud/
│   ├── ringcentral/
│   ├── skype-for-business/
│   ├── slack/
│   └── zoom/
├── compliance_report.md     # EML compliance audit report
└── realism_allowlist.json   # Files exempt from the realism validator
```

When adding new `.eml` files: upload to S3 (`make sync-eml`), then add an entry to `app/inspector/answer_key.py`. Files without an entry are excluded from the inspector pool at runtime.

---

### `scripts/` — Build & Content Utility Scripts (App)

| Script | Purpose |
|---|---|
| `build_lambda.sh` | Packages the Flask app into `lambda.zip` |
| `build_registration_worker.sh` | Packages the registration worker into `registration_worker.zip` |
| `build_campaign_mailer.sh` | Packages the campaign mailer Lambda artifact |
| `validate_eml_realism.py` | Checks `.eml` files against baseline realism criteria |
| `audit_eml.py` | Runs a compliance audit on all `.eml` files; outputs `compliance_report.md` |
| `generate_eml_samples.py` | Helper to scaffold new `.eml` sample files |
| `fix_eml_names.py` | Normalises `.eml` filenames |
| `fix_eml_images.py` | Converts linked images to base64 inline encoding |
| `backfill_cohorts.py` | Backfills cohort fields on existing records |
| `generate_management_deck.py` / `.sh` | Generates a management summary presentation |

Infra + migration helpers now live under `phishing-platform-infra/scripts/`.

---

### `phishing-platform-infra/lambda/` — Lambda Function Source

Standalone AWS Lambda functions that handle async background work. Source lives under `phishing-platform-infra/lambda/` alongside the Terraform definitions that deploy them.

#### `registration_worker/` — Async Registration Lambda

1. Student scans a QR code → fills out the registration form
2. Flask app enqueues the request to **SQS**
3. **SNS** triggers this Lambda when the message arrives
4. Lambda creates the user account in DynamoDB and sends a **SES** confirmation email

Key file: `phishing-platform-infra/lambda/registration_worker/handler.py`

#### `campaign_mailer/` — Campaign Mailer Lambda

Processes phishing simulation campaign messages from SQS, fans out SES emails to the target cohort, and records delivery events in DynamoDB + Redis pub/sub.

Key file: `phishing-platform-infra/lambda/campaign_mailer/handler.py`

---

### `nginx/` — Reverse Proxy

Nginx configuration used in both Docker Compose (local dev) and optional Ansible VM deployments:
- Serves `app/static/` directly (bypasses Gunicorn for static assets)
- Proxies all other requests to Gunicorn on port 5000

---

### `phishing-platform-infra/ansible/` — Optional VM Provisioning

Ansible playbooks for deploying the app on a traditional VM (alternative to the Lambda/Terraform path):

```bash
# Provision server dependencies
ansible-playbook -i phishing-platform-infra/ansible/inventory/hosts.ini phishing-platform-infra/ansible/playbooks/provision.yml

# Deploy the Flask app
ansible-playbook -i phishing-platform-infra/ansible/inventory/hosts.ini phishing-platform-infra/ansible/playbooks/deploy.yml
```

See `phishing-platform-infra/ansible/README.md` for required variables.

---

### `.github/workflows/` — CI/CD Pipelines

| Workflow | Trigger | Purpose |
|---|---|---|
| `ci.yml` | Push to any branch, PRs to `main` | Lint (flake8), validate EML, test (pytest + moto), build Lambda artifacts |
| `deploy-dev.yml` | Push to `main` | Runs CI → `terraform plan` → `terraform apply` → sync S3 → seed DynamoDB |
| `deploy-prod.yml` | Manual dispatch | Same flow targeting `prod` environment (requires approval) |
| `destroy.yml` | Manual dispatch | Tears down all Terraform-managed AWS resources |
| `claude.yml` | PR / issue events | Claude AI agent automation |
| `code-review.yml` | PR events | Review-context summary for main-bound pull requests |

Terraform steps inside these workflows now run from `phishing-platform-infra/terraform`. When splitting repos, copy the deploy/destroy workflows into the infra repo and keep `ci.yml` in the app repo.

All AWS access uses **OIDC** — no static AWS keys are stored in GitHub secrets.

---

## Email Sample Library

The inspector contains phishing emails impersonating these widely-used platforms and services:

<p align="center">
  <img src="app/static/images/logos/microsoft.svg" width="55" title="Microsoft" alt="Microsoft" />&nbsp;&nbsp;
  <img src="app/static/images/logos/google.svg" width="55" title="Google" alt="Google" />&nbsp;&nbsp;
  <img src="app/static/images/logos/amazon.svg" width="55" title="Amazon" alt="Amazon" />&nbsp;&nbsp;
  <img src="app/static/images/logos/slack.svg" width="55" title="Slack" alt="Slack" />&nbsp;&nbsp;
  <img src="app/static/images/logos/zoom.svg" width="55" title="Zoom" alt="Zoom" />&nbsp;&nbsp;
  <img src="app/static/images/logos/adobe.svg" width="55" title="Adobe" alt="Adobe" />&nbsp;&nbsp;
  <img src="app/static/images/logos/apple.svg" width="55" title="Apple" alt="Apple" />&nbsp;&nbsp;
  <img src="app/static/images/logos/paypal.svg" width="55" title="PayPal" alt="PayPal" />&nbsp;&nbsp;
  <img src="app/static/images/logos/netflix.svg" width="55" title="Netflix" alt="Netflix" />&nbsp;&nbsp;
  <img src="app/static/images/logos/dhl.svg" width="55" title="DHL" alt="DHL" />&nbsp;&nbsp;
  <img src="app/static/images/logos/fedex.svg" width="55" title="FedEx" alt="FedEx" />
</p>

| Category | Examples |
|---|---|
| Fake Invoice | PayPal, Microsoft, FedEx, Apple receipt spoofs |
| Impersonation | Voice message, SharePoint, Zoom, IT Helpdesk |
| Urgency | DocuSign, OneDrive, VPN security incident |
| Legit App Impersonation | Slack, Adobe, GitHub-style |
| Punycode / Typosquatting | Google, generic homograph attacks |
| Spam | Marketing, logistics, newsletter, coupon, QR, survey |
| Advanced Techniques | Thread hijacking, pixel tracking, callback phishing, SSO spoof, lateral phishing |
| LINKSEC Templates | AWS, BlueJeans, Cisco Webex, Google Cloud, Microsoft Azure, Office 365, Teams, Oracle, RingCentral, Skype, Slack, Zoom |

The ground truth for all 130 classified emails lives in [`app/inspector/answer_key.py`](app/inspector/answer_key.py). Admins can override individual email classifications and signal lists at runtime via the Answer Key Editor in the dashboard — no code deployment needed.

---

## DynamoDB Schema

| Table | Purpose |
|---|---|
| `users` | Login credentials + cohort fields (class/year/major/facility), inspector state (submitted list + locked flag) |
| `quizzes` | Quiz definitions with embedded questions array and video URL |
| `attempts` | Quiz scores + cohort fields for analytics (one per user per quiz, enforced by condition expression) |
| `responses` | Per-question answers for detailed reporting |
| `inspector_attempts` | Authenticated email classification attempts (legacy; new flow uses anon table) |
| `inspector_attempts_anon` | GDPR-safe anonymous inspector attempts (no username) |
| `bugs` | User-submitted bug reports with status tracking |
| `answer_key_overrides` | Admin-editable overrides merged with `answer_key.py` at runtime |
| `cohort_tokens` | QR self-registration tokens with 90-day TTL |
| `threat_cache` | OpenPhish feed cache with TTL (Redis/DynamoDB hybrid) |
| `campaigns` | Phishing simulation campaign definitions and status |
| `campaign_events` | Delivery/open/click/validation audit trail for campaigns |

All tables use **PAY_PER_REQUEST** (on-demand) billing. Table names are configured via environment variables — see `config.py`.

---

## Quick Start (Local)

```bash
# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt

# Start DynamoDB Local
docker run -d -p 8766:8000 amazon/dynamodb-local

# Configure env and seed
export DYNAMODB_ENDPOINT=http://localhost:8766
export AWS_REGION_NAME=eu-west-3
export AWS_ACCESS_KEY_ID=fake
export AWS_SECRET_ACCESS_KEY=fake
export DYNAMODB_USERS=phishing-app-dev-users
export DYNAMODB_QUIZZES=phishing-app-dev-quizzes
export DYNAMODB_ATTEMPTS=phishing-app-dev-attempts
export DYNAMODB_RESPONSES=phishing-app-dev-responses
export DYNAMODB_INSPECTOR=phishing-app-dev-inspector-attempts
export DYNAMODB_INSPECTOR_ANON=phishing-app-dev-inspector-attempts-anon
export DYNAMODB_BUGS=phishing-app-dev-bugs
export DYNAMODB_ANSWER_KEY_OVERRIDES=phishing-app-dev-answer-key-overrides
export DYNAMODB_COHORT_TOKENS=phishing-app-dev-cohort-tokens
export DYNAMODB_THREAT_CACHE=phishing-app-dev-threat-cache
export DYNAMODB_CAMPAIGNS=phishing-app-dev-campaigns
export DYNAMODB_CAMPAIGN_EVENTS=phishing-app-dev-campaign-events
export S3_BUCKET=phishing-app-dev-eu-west-3
export SQS_CAMPAIGN_QUEUE_URL=https://sqs.eu-west-3.amazonaws.com/123456789012/phishing-app-dev-campaigns
export SECRET_KEY=dev-secret
python seed_dynamodb.py

# Run the development server
python run.py
```

App runs at **http://localhost:5000**. Default admin: `admin` / `admin123`

**Troubleshooting:**
- **PEP 668 / externally-managed-environment**: use a venv (`python3 -m venv .venv`) instead of system Python.
- **`lambda.zip` missing**: run `./scripts/build_lambda.sh`.
- **AWS profile issues**: set `AWS_PROFILE=terraform-deployer` before Terraform.
- **Videos not loading on Lambda**: set `VIDEO_BASE_URL` to an S3/CloudFront base URL and re-run `seed_dynamodb.py`.
  - Example: `VIDEO_BASE_URL=https://phishing-app-dev-eu-west-3.s3.eu-west-3.amazonaws.com/videos`
  - Upload: `make sync-assets` (requires Terraform state) or: `aws s3 sync app/static/videos/ s3://phishing-app-dev-eu-west-3/videos/ --exclude "*" --include "*.mp4" --region eu-west-3`

---

## Docker Compose (recommended for local dev)

```bash
# Build and start all services (Nginx :80 -> Gunicorn -> Flask -> DynamoDB Local :8766)
docker compose up -d --build

# Create tables and seed the database
python setup_local_db.py                         # creates all 9 DynamoDB tables
docker compose exec web python seed_dynamodb.py  # seeds admin user + quizzes

# Stop
docker compose down
```

Access at **http://localhost** (port 80). The compose stack runs three services:

| Service | Image | Purpose |
|---|---|---|
| `dynamodb-local` | amazon/dynamodb-local | In-memory DynamoDB on port 8766 |
| `web` | Local Dockerfile | Gunicorn + Flask app |
| `nginx` | nginx:alpine | Reverse proxy + static assets on port 80 |

---

## Make Targets

```bash
make lint                  # flake8 --max-line-length=120
make test                  # pytest + moto (JUnit XML report)
make lambda                # build lambda.zip
make registration-worker   # build registration_worker.zip
make campaign-mailer       # build campaign_mailer.zip
make validate-eml          # validate .eml file realism
make sync-eml              # sync examples/*.eml -> S3 eml-samples/
make sync-assets           # sync app/static/videos/*.mp4 -> S3 videos/
make audit-eml             # run compliance audit, generate report
```

> **Uploading EML samples manually:**
> ```bash
> aws s3 sync examples/ s3://phishing-app-dev-eu-west-3/eml-samples/ \
>   --exclude "*" --include "*.eml" --region eu-west-3
> ```
> After uploading, add a corresponding entry to `app/inspector/answer_key.py`.

---

## CI/CD Overview

**`ci.yml`** — runs on every push and PR to `main`:
1. Lint (flake8) + EML realism validation
2. Tests (pytest + moto) — JUnit XML uploaded as artifact
3. Build `lambda.zip` and `registration_worker.zip`

**`deploy-dev.yml`** — auto-deploys on push to `main`:
1. Runs CI (`ci.yml`)
2. Bootstraps IAM (idempotent `terraform import` of OIDC provider + deploy role)
3. `terraform plan` → uploads plan artifact
4. `terraform apply` — all AWS infrastructure
5. Syncs EML samples and video assets to S3
6. Seeds DynamoDB (skip with `skip_seed=true` input)

**`deploy-prod.yml`** — manual `workflow_dispatch`:
- Same build → plan → apply flow targeting the `prod` GitHub environment
- Requires environment approval rules to be configured

**`destroy.yml`** — manual teardown:
- Removes IAM resources from Terraform state (so the deploy role survives for future CI)
- Optional S3 bucket emptying for versioned buckets

All workflows use **OIDC** to assume the deploy role — no static AWS keys in GitHub secrets. Set `AWS_DEPLOY_ROLE_ARN` and `TF_VAR_SECRET_KEY` as GitHub Actions secrets.

---

## AWS Deployment

Full Terraform + AWS deployment guide: [`documentation/operator/DEPLOYMENT.md`](documentation/operator/DEPLOYMENT.md)

### Bootstrap Terraform remote state (one-time)

```bash
cd phishing-platform-infra/terraform/bootstrap
terraform init
terraform apply \
  -var="state_bucket_name=phishing-terraform-state" \
  -var="lock_table_name=phishing-terraform-locks" \
  -var="aws_region=eu-west-3"
```

### GitHub Actions secrets

| Secret | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | Output of `terraform output github_actions_deploy_role_arn` |
| `TF_VAR_SECRET_KEY` | Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"` |

Create `dev` and `prod` environments at **Settings → Environments**.

### Dev → Prod data migration

```bash
# Migrate S3 buckets and DynamoDB tables (preserves password hashes)
./phishing-platform-infra/scripts/migrate_s3.sh
python3 ./phishing-platform-infra/scripts/migrate_dynamodb.py --from dev --to prod

# Dry run first
MIGRATE_DRY_RUN=true ./phishing-platform-infra/scripts/migrate_s3.sh
MIGRATE_DRY_RUN=true python3 ./phishing-platform-infra/scripts/migrate_dynamodb.py --from dev --to prod --dry-run
```

---

## Documentation Index

| Guide | Audience | Description |
|---|---|---|
| [Workboard](documentation/WORKBOARD.md) | Maintainers | Live milestone, issue, and branch map for the deep-scan backlog |
| [Architecture](documentation/ARCHITECTURE.md) | All | 10 Mermaid diagrams: system, AWS infra, schema, CI/CD, flows |
| [Requirements](documentation/REQUIREMENTS.md) | All | Infrastructure, functional & IAM requirements |
| [Audit & Roadmap](documentation/AUDIT_AND_ROADMAP.md) | All | Known issues + upcoming feature roadmap |
| [GDPR Compliance](documentation/GDPR_COMPLIANCE.md) | All | Anonymous tables, data retention, privacy notes |
| [AWS Improvements](documentation/AWS_IMPROVEMENTS.md) | All | Cost and architecture optimisation proposals |
| [Compliance Frameworks](documentation/COMPLIANCE_FRAMEWORKS.md) | All | ISO 27001, NIST, GDPR mapping |
| [Feature Proposals](documentation/FEATURE_PROPOSALS.md) | All | Ideas for future enhancements |
| | | |
| [Developer Guide](documentation/dev/README.md) | Developers | Index of all dev docs |
| [Local Setup](documentation/dev/SETUP.md) | Developers | Docker Compose + DynamoDB Local setup |
| [Contributing](documentation/dev/CONTRIBUTING.md) | Developers | How to contribute code or email samples |
| [Adding EML Files](documentation/dev/ADDING_EML_FILES.md) | Developers | Expand the email sample library |
| [Adding Quizzes](documentation/dev/ADDING_QUIZZES.md) | Developers | Create new quiz modules |
| [Dev Architecture](documentation/dev/ARCHITECTURE.md) | Developers | Internal implementation details |
| | | |
| [Student Guide](documentation/user/STUDENT_GUIDE.md) | Students | How to use quizzes and the inspector |
| [Admin Guide](documentation/user/ADMIN_GUIDE.md) | Admins | Dashboard operations & user management |
| | | |
| [Operator Guide](documentation/operator/README.md) | Operators | Index of all operator docs |
| [Deployment](documentation/operator/DEPLOYMENT.md) | Operators | Step-by-step Terraform + AWS deploy |
| [Infrastructure](documentation/operator/INFRASTRUCTURE.md) | Operators | AWS resource reference |
| [CI/CD](documentation/operator/CICD.md) | Operators | GitHub Actions workflow details |
| [Maintenance](documentation/operator/MAINTENANCE.md) | Operators | Operational tasks (seeding, migrations, resets) |

---

## Workboard

Use [`documentation/WORKBOARD.md`](documentation/WORKBOARD.md) as the backlog source of truth. It links each milestone cluster to its initiative issue, sub-issues, confirmed bugs, and the branch naming pattern expected for follow-up work.

---

## Admin Operations Guide

### Import Students (CSV)

1. Log in as admin → **Admin → Import Users**
2. Upload a CSV with these required columns:

```csv
username,email,password,class,academic_year,major,facility,group
jdoe,jdoe@school.edu,TempPass123,Class A,2025,CS,Paris,engineering
asmith,asmith@school.edu,TempPass456,Class B,2025,Marketing,Lyon,marketing
```

All columns are mandatory. `group` defaults to `default` if omitted.

### QR Code Self-Registration

1. Log in as admin → **Admin → Generate QR Code**
2. Submit the form to generate a QR linking to `/auth/register`
3. Download and share/print the PNG
4. Students scan → fill out the form → receive a SES confirmation email once the Lambda worker processes the request

### Upload Email Samples (.eml)

```bash
aws s3 sync examples/ s3://phishing-app-<env>-eu-west-3/eml-samples/ \
  --exclude "*" --include "*.eml"
```

After uploading, add corresponding entries to `app/inspector/answer_key.py`.

### Reset Inspector Access

Each user can submit answers for their assigned 8 emails once. After all 8 are submitted the inspector locks. Admins can reset:
- A single user: **Admin → Inspector Analytics → Reset User**
- By cohort or all users: bulk reset filters in the same view

### GDPR Migration (legacy inspector data)

If you have older inspector attempts containing usernames, migrate them to the anonymous table:

```bash
python3 phishing-platform-infra/scripts/migrate_inspector_attempts.py --dry-run
python3 phishing-platform-infra/scripts/migrate_inspector_attempts.py
```

### Download Reports

1. **Admin → Reports** — quiz / cohort CSV reports
2. **Admin → Inspector Analytics** — inspector cohort CSV reports
3. Click **Download CSV** — receive a pre-signed S3 link (valid 15 minutes)

---

## Improving Example Emails (Realism Checklist)

To make `examples/` feel closer to real-world phishing:
- **Multipart emails**: include both `text/plain` and `text/html` parts
- **HTML layout**: tables, buttons, brand colors, footer/legal text
- **Inline images**: CID-embedded logos + remote image references
- **QR codes**: embedded QR image pointing to a test URL
- **Tracking pixels**: 1x1 image to mimic open tracking
- **Attachments**: PDF invoices, HTML files, or ZIPs (benign placeholders)
- **Header realism**: `Reply-To` mismatch, `Return-Path` mismatch, SPF/DKIM/DMARC results
- **Look-alike domains**: subdomain tricks and homographs (punycode)
- **Urgency + social engineering**: time pressure, authority cues, or fear

Run the validator before committing:

```bash
make validate-eml   # writes examples/realism_report.json
```

Files that should legitimately skip a check: add them to `examples/realism_allowlist.json`.

**Reference datasets:**
- https://github.com/SeanWrightSec/phishing-examples
- https://github.com/sunknighteric/EPVME-Dataset
- https://github.com/rokibulroni/Phishing-Email-Dataset

> Always review licenses and strip any real personal data before using samples in `examples/`.

---

## Contributing

Contributions are welcome — new email samples, quiz questions, UI improvements, and infrastructure improvements. Please read [`documentation/dev/CONTRIBUTING.md`](documentation/dev/CONTRIBUTING.md) before opening a pull request.

This project is released under **CC0** (public domain). Use it freely.

---

## Changelog & License

- Full version history: [CHANGELOG.md](CHANGELOG.md)
- Current version: **1.2.5**
- License: **CC0** — no rights reserved

---

<p align="center">
  Built with care for ESME engineering school<br/>
  <a href="https://buymeacoffee.com/santiagogow">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee" />
  </a>
</p>
