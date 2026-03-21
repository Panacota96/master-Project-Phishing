# Master-Project-Phishing

A **phishing awareness training web application** built with Flask, created as part of the ESME engineering school Master Project.

Users take interactive quizzes to learn how to identify phishing emails, and can inspect real-world phishing samples using the built-in Email Threat Inspector.

## Requirements

**Runtime:** Python 3.12, Terraform >= 1.5, AWS CLI v2, Docker + Compose.
**Python deps:** Flask 3.1, Flask-Login, Flask-WTF, Werkzeug, boto3 1.35, mangum, gunicorn, qrcode[pil], aws-xray-sdk (see `requirements.txt`).
**AWS:** Lambda (512 MB app + 256 MB registration worker), API Gateway v2, CloudFront, S3, DynamoDB (9 tables), SQS (+ DLQ), SES, SNS (2 topics), CloudWatch alarms + dashboard, X-Ray, Route 53 (optional).
**IAM:** Lambda execution role + Registration Worker role + GitHub Actions OIDC deploy role — see [`documentation/REQUIREMENTS.md`](documentation/REQUIREMENTS.md) for the full permissions list.
**Architecture:** System overview, AWS infrastructure, data flows, and CI/CD pipeline — see [`documentation/ARCHITECTURE.md`](documentation/ARCHITECTURE.md) (10 Mermaid diagrams).
**Tests:** `make test` (pytest + moto, no real AWS needed) · `make lint` (flake8, max-line-length=120).

## Features

### Phishing Quiz
- Multiple-choice quizzes covering phishing techniques (URL analysis, spoofing, urgency tactics, CEO fraud, smishing, MFA, etc.)
- Explanations after each question showing why an email is phishing or legitimate
- Progress bar, color-coded score summary, rank badge, and quiz history per user
- Each quiz requires watching a training video before starting
- Quizzes are defined in DynamoDB and seeded via `seed_dynamodb.py`

### Email Threat Inspector
- Standalone tool at `/inspector/` for analyzing real `.eml` files
- Parses and displays: message overview, full headers, HTML preview (sandboxed), extracted links, attachments, and security warnings
- Users classify each email as Spam or Phishing and select phishing signals
- Per-session pool of up to 8 emails (1–3 spam + phishing) sampled from S3
- Required signal count per email is dynamic (driven by the answer key, not hardcoded)
- 10 phishing signal categories: Impersonation, Typosquatting/Punycodes, External Sender Domain, Spoofing, Social Engineering, Urgency, Fake Invoice, Malicious Attachment, Fake Login Page, Side Channel Communication
- Answers saved to GDPR-safe anonymous table (no username stored)

### Admin Dashboard
- Stats overview: total users, total attempts, average score, score distribution chart
- Per-quiz statistics, cohort analytics, inspector signal accuracy
- Real-time stats polling and OpenPhish threat feed widget
- Risk Dashboard: per-cohort risk score combining quiz failure rate and signal miss rate
- CSV report generation with pre-signed S3 download links
- Answer key editor: change any email's classification and signals without a code deployment

### Authentication
- Login / Logout with form validation and password hashing (Werkzeug)
- Admin vs regular user roles (`is_admin` flag)
- No public self-registration in the navbar — accounts created by admins only
- Admin can bulk-import students via CSV upload
- Admin can generate a QR code linking to the self-registration page
- Self-registration enqueues to SQS → Lambda worker creates user + sends SES confirmation email
- Students can change their own password

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask (Python 3.12), Flask-Login, Flask-WTF |
| Database | DynamoDB (AWS) — 9 tables |
| Frontend | Jinja2 + Bootstrap 5 (CDN) |
| Charts | Chart.js |
| EML Parsing | Python `email` stdlib (no extra dependencies) |
| QR Codes | qrcode[pil] |
| Async Workers | AWS SQS + Lambda (registration worker) |
| Email | AWS SES |
| Deployment | AWS Lambda + API Gateway + CloudFront + Terraform (CI/CD via GitHub Actions) |

## Quick Start (Local)

```bash
# Create and activate venv (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt

# Start DynamoDB Local
docker run -d -p 8766:8000 amazon/dynamodb-local

# Configure local DynamoDB + seed
export DYNAMODB_ENDPOINT=http://localhost:8766
export AWS_REGION_NAME=eu-west-3
export AWS_ACCESS_KEY_ID=fake
export AWS_SECRET_ACCESS_KEY=fake
export DYNAMODB_USERS=en-garde-dev-users
export DYNAMODB_QUIZZES=en-garde-dev-quizzes
export DYNAMODB_ATTEMPTS=en-garde-dev-attempts
export DYNAMODB_RESPONSES=en-garde-dev-responses
export DYNAMODB_INSPECTOR=en-garde-dev-inspector-attempts
export DYNAMODB_INSPECTOR_ANON=en-garde-dev-inspector-attempts-anon
export DYNAMODB_BUGS=en-garde-dev-bugs
export DYNAMODB_ANSWER_KEY_OVERRIDES=en-garde-dev-answer-key-overrides
export DYNAMODB_COHORT_TOKENS=en-garde-dev-cohort-tokens
export S3_BUCKET=en-garde-dev
export SECRET_KEY=dev-secret
python seed_dynamodb.py

# Run the development server
python run.py
```

The app runs at **http://localhost:5000**. Default admin: `admin` / `admin123`

## Docker Compose (recommended for local dev)

```bash
# Build and start (Nginx on port 80 -> Gunicorn -> Flask -> DynamoDB Local)
docker compose up -d --build

# Create tables and seed the database
python setup_local_db.py   # creates all 9 DynamoDB tables
docker compose exec web python seed_dynamodb.py

# Stop
docker compose down
```

Access at **http://localhost** (port 80).

## Reproducible Setup (Checklist)
1. Create and activate a virtual environment: `python3 -m venv .venv && source .venv/bin/activate`
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Start DynamoDB Local and set env vars (see Quick Start above)
4. Seed data: `python seed_dynamodb.py`
5. Run locally: `python run.py`
6. Verify login and quiz list load in the browser.

## Troubleshooting
- **PEP 668 / externally-managed-environment**: use a venv (`python3 -m venv .venv`) instead of system Python.
- **`lambda.zip` missing**: run `./scripts/build_lambda.sh`.
- **AWS profile issues**: set `AWS_PROFILE=terraform-deployer` before Terraform.
- **Videos not loading on Lambda**: set `VIDEO_BASE_URL` to an S3/CloudFront base URL and re-run `seed_dynamodb.py`.
  - Example: `VIDEO_BASE_URL=https://en-garde-dev-eu-west-3.s3.eu-west-3.amazonaws.com/videos`
  - Upload: `aws s3 sync app/static/videos/ s3://en-garde-dev-eu-west-3/videos/`
  - Ensure the bucket policy allows public read for `videos/*`.

## Make Targets

```bash
make lint                  # flake8 --max-line-length=120
make test                  # pytest + moto
make lambda                # build lambda.zip
make registration-worker   # build registration_worker.zip
make validate-eml          # validate EML realism
make sync-assets           # sync EML + video assets to S3
```

## CI/CD Overview

**Continuous Integration (`ci.yml`)** runs on every branch push and PR to main:
- Linting (flake8)
- EML realism validation (`make validate-eml`)
- Automated tests (pytest + moto) — JUnit XML report uploaded as artifact
- Lambda artifact build (`lambda.zip` + `registration_worker.zip`)

**Continuous Deployment (`deploy-dev.yml`)** runs automatically on push to `main`:
1. Runs CI first (calls `ci.yml`)
2. Bootstraps IAM: imports OIDC provider + GitHub Actions role if orphaned, applies the deploy policy, waits 20 s for propagation
3. `terraform plan` — uploads plan artifact
4. `terraform apply` — deploys all AWS infrastructure
5. Syncs EML samples and video assets to S3
6. Seeds DynamoDB (skippable via `skip_seed` input)

**Production Deployment (`deploy-prod.yml`)** is manual (`workflow_dispatch`):
- Same build → plan → apply flow targeting the `prod` environment
- Requires the `prod` GitHub environment to be configured with approval rules

**Infrastructure teardown (`destroy.yml`)** is manual:
- Removes IAM resources from Terraform state before destroy (so they survive for future CI)
- Optional S3 bucket emptying step for versioned buckets

**GitHub Actions uses OIDC** to assume the deploy role — no static AWS keys needed.
Set the `skip_seed` workflow input to `true` to skip DynamoDB seeding on manual dispatch.

## Admin Operations Guide

### Upload Users (CSV)
1. Log in as an admin.
2. Go to **Admin → Import Users**.
3. Upload a CSV with these required columns:
   - `username`, `email`, `password`, `class`, `academic_year`, `major`, `facility` (all mandatory)
   - Optional: `group` (defaults to `default`)
4. Click **Import Users** and confirm the import summary.

Example CSV:
```csv
username,email,password,class,academic_year,major,facility,group
jdoe,jdoe@school.edu,TempPass123,Class A,2025,CS,Paris,engineering
asmith,asmith@school.edu,TempPass456,Class B,2025,Marketing,Lyon,marketing
```

### QR Code Self-Registration
1. Log in as an admin.
2. Go to **Admin → Generate QR Code**.
3. Submit the form to generate a QR code linking to `/auth/register`.
4. Download and share/print the PNG.
5. Students scan the QR code, fill out the registration form, and receive a confirmation email once the Lambda worker processes their request.

### Upload Email Samples (.eml)
Use S3 and keep files under the `eml-samples/` prefix:
```bash
aws s3 sync examples/ s3://en-garde-<env>-eu-west-3/eml-samples/ --exclude "*" --include "*.eml"
```
After uploading, add corresponding entries to `app/inspector/answer_key.py`.

### Migrate Inspector Attempts to GDPR-Safe Table
If you have legacy inspector attempts with usernames, migrate them to the anonymous table:
```bash
python3 scripts/migrate_inspector_attempts.py --dry-run
python3 scripts/migrate_inspector_attempts.py
```

## Improving Example Emails (Realism Checklist)
To make the `examples/` folder feel closer to real-world phishing, aim for:
- **Multipart emails**: include both `text/plain` and `text/html`.
- **HTML layout**: tables, buttons, brand colors, and footer/legal text.
- **Inline images**: use CID-embedded logos (`Content-ID`) plus remote image references.
- **QR codes**: embed a QR image (CID or remote) that points to a test URL.
- **Tracking pixels**: a 1x1 image to mimic open tracking.
- **Attachments**: PDF invoices, HTML files, or ZIPs (benign placeholders).
- **Header realism**: `Reply-To` mismatch, `Return-Path` mismatch, SPF/DKIM/DMARC results.
- **Look-alike domains**: subdomain tricks and homographs (punycode) in links.
- **Urgency + social engineering language**: time pressure, authority, or fear cues.

### Realism Validator
Run the built-in validator to ensure all example emails meet baseline realism:
```bash
make validate-eml
```
Reports are written to `examples/realism_report.json`.
If a file should skip a check, add it to `examples/realism_allowlist.json`.

### Reference Datasets / Repos
These GitHub projects can be used as inspiration or sources for realistic examples:
- https://github.com/SeanWrightSec/phishing-examples
- https://github.com/sunknighteric/EPVME-Dataset
- https://github.com/rokibulroni/Phishing-Email-Dataset

**Note:** Always review licenses and remove any sensitive or personal data from real samples before using them in `examples/`.

### Download Reports
1. Log in as admin.
2. Go to **Admin → Reports** to generate quiz/cohort reports.
3. Go to **Admin → Inspector Analytics** to download inspector cohort reports.
4. Click the **Download CSV** button; you'll receive a pre-signed S3 link.

### Inspector Lockout
Each user can submit answers for the assigned 8 emails once. After completing all 8, the Inspector is locked until an admin resets access in **Admin → Inspector Analytics**. Admins can reset a single user or bulk reset by cohort filters or all users.

## DynamoDB Usage Summary

| Table | Purpose |
|---|---|
| Users | Login credentials + cohort fields (class/year/major/facility), inspector state (submitted list + locked flag) |
| Quizzes | Quiz definitions with embedded questions array and video URL |
| Attempts | Quiz scores + cohort fields for analytics (one per user per quiz, enforced by condition expression) |
| Responses | Per-question answers for detailed reporting |
| Inspector attempts | Authenticated email classification attempts + cohort fields (legacy; new flow uses anon table) |
| Inspector attempts (anon) | GDPR-safe anonymous inspector attempts (no username) |
| Bugs | User-submitted bug reports with status tracking |
| Answer key overrides | Admin-editable overrides for email classification and signals; merged with `answer_key.py` at runtime |
| Cohort tokens | QR registration tokens with 90-day TTL |

## Lambda Build

```bash
# Build Flask app artifact
./scripts/build_lambda.sh   # or: make lambda

# Build registration worker artifact
make registration-worker
```

## AWS Deployment

See `documentation/operator/DEPLOYMENT.md` for the full Terraform + AWS deployment guide.

## Dev to Prod Migration (Snapshot)
Use these scripts to migrate data from dev to prod while keeping password hashes:

```bash
./scripts/migrate_s3.sh
python3 ./scripts/migrate_dynamodb.py --from dev --to prod
```

Optional dry-run (no writes):
```bash
MIGRATE_DRY_RUN=true ./scripts/migrate_s3.sh
MIGRATE_DRY_RUN=true python3 ./scripts/migrate_dynamodb.py --from dev --to prod --dry-run
```

## Terraform Remote State (Bootstrap)

```bash
cd terraform/bootstrap
terraform init
terraform apply \
  -var="state_bucket_name=phishing-terraform-state" \
  -var="lock_table_name=phishing-terraform-locks" \
  -var="aws_region=eu-west-3"
```

## CI/CD Environment Variables

Set these in GitHub Actions (Settings -> Secrets and variables -> Actions):

**Secrets:**
- `AWS_DEPLOY_ROLE_ARN` — IAM role ARN for OIDC deploy (output from `terraform output github_actions_deploy_role_arn`)
- `TF_VAR_SECRET_KEY` — Flask secret key (generate with `python3 -c "import secrets; print(secrets.token_hex(32))"`)

**Environments:** Create `dev` and `prod` environments at Settings -> Environments.

## Project Structure

```
master-Project-Phishing/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # DynamoDB data access layer (all table operations)
│   ├── auth/                # Login, register, logout, QR, CSV import, change-password
│   ├── quiz/                # Quiz list, video gate, take quiz, finish, history
│   ├── dashboard/           # Admin stats, analytics, reports, answer key editor, risk
│   ├── inspector/           # Email Threat Inspector (EML parsing + JSON API)
│   │   └── answer_key.py    # Static ground-truth baseline (classification + signals)
│   ├── templates/           # Jinja2 templates (base, auth, quiz, dashboard, inspector)
│   └── static/              # CSS, JS, video assets
├── tests/                   # Pytest suite (moto-mocked AWS)
├── scripts/                 # Migration, build, and utility scripts
├── terraform/               # IaC: Lambda x2, API Gateway, CloudFront, DynamoDB, S3,
│                            #      SQS, SNS, SES, CloudWatch, IAM, OIDC
├── aws/                     # AWS EC2 deployment guide
├── nginx/                   # Nginx reverse proxy config
├── documentation/           # Full docs suite (dev, user, operator, compliance)
├── Dockerfile               # Python 3.12-slim + Gunicorn
├── docker-compose.yml       # Web + Nginx + DynamoDB Local services
├── seed_dynamodb.py         # DynamoDB seeder (admin user + quizzes)
├── setup_local_db.py        # Creates DynamoDB tables for local dev
├── config.py                # App configuration (env var mapping)
├── run.py                   # Local dev entry point
├── requirements.txt         # Python dependencies
├── VERSION                  # Current version number
├── CHANGELOG.md             # Version history
└── CLAUDE.md                # AI assistant context
```

## Email Samples

The answer key covers phishing across several attack categories:

| Category | Examples |
|---|---|
| Fake Invoice | PayPal, Microsoft, FedEx, Apple receipt |
| Impersonation | Voice message, SharePoint, Zoom, IT Helpdesk |
| Urgency | DocuSign, OneDrive, VPN security incident |
| Legit App Impersonation | Slack, Adobe, GitHub-style |
| Punycode / Typosquatting | Google, generic homograph attacks |
| Spam | Marketing, logistics, newsletter, coupon, QR, survey |
| Advanced | Thread hijacking, pixel tracking, callback phishing, SSO spoof, lateral phishing |
| LINKSEC templates | AWS, BlueJeans, Cisco Webex, Google Cloud, Microsoft, Slack, Zoom, etc. |

## Ansible (Optional VM Deploy)
Use Ansible to provision a VM and deploy the Flask app with Gunicorn + Nginx.
- Provision: `ansible-playbook -i ansible/inventory/hosts.ini ansible/playbooks/provision.yml`
- Deploy: `ansible-playbook -i ansible/inventory/hosts.ini ansible/playbooks/deploy.yml`
See `ansible/README.md` for required variables.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

CC0
