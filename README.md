# Master-Project-Phishing

A **phishing awareness training web application** built with Flask, created as part of the ESME engineering school Cloud SecDevOps course (TP1/TP2).

Users take interactive quizzes to learn how to identify phishing emails, and can inspect real-world phishing samples using the built-in Email Threat Inspector.

## Features

### Phishing Quiz
- Multiple-choice quizzes covering phishing techniques (URL analysis, spoofing, urgency tactics, CEO fraud, smishing, MFA, etc.)
- Explanations after each question showing why an email is phishing or legitimate
- Progress bar, color-coded score summary, and quiz history per user

### Email Threat Inspector
- Standalone tool at `/inspector/` for analyzing real `.eml` files
- Parses and displays: message overview, full headers, HTML preview (sandboxed), extracted links, attachments, and security warnings
- Users classify each email as Spam or Phishing and select phishing signals
- Immediate feedback with correct/incorrect indicators and CTF flags
- 10 phishing signal categories: Impersonation, Typosquatting/Punycodes, External Sender Domain, Spoofing, Social Engineering, Urgency, Fake Invoice, Malicious Attachment, Fake Login Page, Side Channel Communication

### Admin Dashboard
- Stats overview: total users, total attempts, average score
- Score distribution bar chart (Chart.js)
- Per-quiz statistics and recent activity tables

### Authentication
- Register / Login / Logout with form validation
- Password hashing (Werkzeug)
- Admin vs regular user roles

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask (Python 3.12), Flask-Login, Flask-WTF |
| Database | DynamoDB (AWS) |
| Frontend | Jinja2 + Bootstrap 5 (CDN) |
| Charts | Chart.js |
| EML Parsing | Python `email` stdlib (no extra dependencies) |
| Deployment | AWS Lambda + API Gateway + Terraform (CI/CD via GitLab) |

## Quick Start (Local)

```bash
# Create and activate venv (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt

# Start DynamoDB Local (optional, for local dev)
docker run -d -p 8000:8000 amazon/dynamodb-local

# Configure local DynamoDB + seed
export DYNAMODB_ENDPOINT=http://localhost:8000
export AWS_REGION_NAME=eu-west-3
export AWS_ACCESS_KEY_ID=fake
export AWS_SECRET_ACCESS_KEY=fake
export DYNAMODB_USERS=phishing-app-dev-users
export DYNAMODB_QUIZZES=phishing-app-dev-quizzes
export DYNAMODB_ATTEMPTS=phishing-app-dev-attempts
export DYNAMODB_RESPONSES=phishing-app-dev-responses
export DYNAMODB_INSPECTOR=phishing-app-dev-inspector-attempts
export S3_BUCKET=phishing-app-dev
export SECRET_KEY=dev-secret
python seed_dynamodb.py

# Run the development server
python run.py
```

The app runs at **http://localhost:5000**. Default admin: `admin` / `admin123`

## Reproducible Setup (Checklist)
1. Create and activate a virtual environment: `python3 -m venv .venv && source .venv/bin/activate`
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Seed data: `python seed_dynamodb.py` (DynamoDB)
4. Run locally: `python run.py`
5. Verify login and quiz list load in the browser.

## Troubleshooting
- **PEP 668 / externally-managed-environment**: use a venv (`python3 -m venv .venv`) instead of system Python.
- **`lambda.zip` missing**: run `./scripts/build_lambda.sh`.
- **AWS profile issues**: set `AWS_PROFILE=terraform-deployer` before Terraform.

## Make Targets

```bash
make lint
make test
make lambda
```

## CI/CD Notes
- GitLab CI expects `TF_VAR_secret_key` to be set as a masked variable.
- GitLab CI uses `TF_ENV` (`dev` or `prod`) to select the backend and tfvars file.
- Set `SKIP_SEED=true` to skip DynamoDB seeding during deploy.
- Test reports are emitted as `report.xml` for JUnit artifacts.

## CI/CD Overview
**Continuous Integration (CI)** automatically checks every change:
- Linting (code quality)
- Automated tests
- Build the Lambda artifact

**Continuous Deployment (CD)** manages infrastructure safely:
- Terraform plan to preview changes
- Dev deploy is automatic, prod deploy is manual


## Admin Operations Guide

### Upload Users (CSV)
1. Log in as an admin.
2. Go to **Admin → Import Users**.
3. Upload a CSV with these required columns:
   - `username`, `email`, `password`, `class`, `academic_year`, `major`
   - Optional: `group`
4. Click **Import Users** and confirm the import summary.

Example CSV:
```csv
username,email,password,class,academic_year,major,group
jdoe,jdoe@school.edu,TempPass123,Class A,2025,CS,engineering
asmith,asmith@school.edu,TempPass456,Class B,2025,Marketing,marketing
```

### Upload Email Samples (.eml)
Use S3 and keep files under the `eml-samples/` prefix:
```bash
aws s3 sync examples/ s3://phishing-app-<env>-eu-west-3/eml-samples/ --exclude "*" --include "*.eml"
```

### Download Reports
1. Log in as admin.
2. Go to **Admin → Reports** to generate quiz/cohort reports.
3. Go to **Admin → Inspector Analytics** to download inspector cohort reports.
4. Click the **Download CSV** button; you’ll receive a pre‑signed S3 link.

## DynamoDB Usage Summary
**Users table**: login credentials + cohort fields (class/year/major).  
**Quizzes table**: quiz definitions and questions.  
**Attempts table**: quiz scores + cohort fields for analytics.  
**Responses table**: per‑question responses for reporting.  
**Inspector attempts table**: email classification attempts + cohort fields.

## Docker

```bash
# Build and start (Nginx on port 80 -> Gunicorn -> Flask)
docker compose up -d --build

# Seed the database
docker compose exec web python seed.py

# Stop
docker compose down
```

Access at **http://localhost** (port 80).

## Lambda Build

Use the shared build script to package the Lambda artifact:

```bash
./scripts/build_lambda.sh
```

## AWS Deployment

See `DEPLOYMENT_GUIDE.md` for the full Terraform + AWS deployment guide.

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

Set these in GitLab CI/CD:

- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`
- `TF_ENV` (`dev` or `prod`)
- `TF_VAR_secret_key` (masked)
- `TF_VAR_app_name` (optional, defaults to `phishing-app`)
- `SKIP_SEED` (optional, `true` to skip seeding)

## Project Structure

```
master-Project-Phishing/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # User, Quiz, Question, Answer, QuizAttempt
│   ├── auth/                # Login, register, logout
│   ├── quiz/                # Quiz list, take quiz, results, history
│   ├── dashboard/           # Admin stats and charts
│   ├── inspector/           # Email Threat Inspector (EML parsing + API)
│   ├── templates/           # Jinja2 templates (base, auth, quiz, dashboard, inspector)
│   └── static/css/          # Custom styles
├── examples/                # 6 real phishing/spam .eml samples
├── Phishing AOC/            # TryHackMe lab reference materials
├── aws/                     # AWS deployment guide and scripts
├── nginx/                   # Nginx reverse proxy config
├── Dockerfile               # Python 3.12-slim + Gunicorn
├── docker-compose.yml       # Web + Nginx services
├── seed.py                  # Database seeder (admin + 10 questions)
├── config.py                # App configuration
├── run.py                   # Entry point
├── requirements.txt         # Python dependencies
├── CHANGELOG.md             # Version history
└── CLAUDE.md                # AI assistant context
```

## Email Samples

Six real `.eml` files from TryHackMe's Advent of Cyber phishing lab:

| Email | Type | Signals |
|-------|------|---------|
| Fake Invoice | Phishing | Fake Invoice, Urgency, Spoofing |
| Impersonation + Attachment | Phishing | Impersonation, Malicious Attachment, Spoofing |
| Impersonation + Urgency | Phishing | Impersonation, Social Engineering, Urgency |
| Legit App Impersonation | Phishing | Impersonation, External Domain, Social Engineering |
| Marketing Spam | Spam | N/A |
| Punycode Attack | Phishing | Punycode, Impersonation, Social Engineering |

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

CC0
