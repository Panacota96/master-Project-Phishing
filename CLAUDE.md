# CLAUDE.md

This file provides guidance to Claude Code, Codex, or any AI assistant working on this repository.

## Project

This is the **master-Project-Phishing** repository, part of an ESME engineering school Cloud SecDevOps course (TP1/TP2). It is a **phishing awareness training web application** built with Flask. The project also includes real-world phishing email samples (`.eml` files) from a TryHackMe Advent of Cyber (AOC) lab for educational analysis.

## Tech Stack

- **Backend**: Flask (Python 3.12), Flask-Login, Flask-WTF
- **Database**: DynamoDB (AWS)
- **Frontend**: Jinja2 templates + Bootstrap 5 (CDN)
- **Charts**: Chart.js
- **Auth**: Flask-Login + Werkzeug password hashing

## Setup & Run (Local Development)

```bash
# Create and activate venv (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt

# Start DynamoDB Local (optional for local dev)
docker run -d -p 8000:8000 amazon/dynamodb-local

# Configure and seed DynamoDB
export DYNAMODB_ENDPOINT=http://localhost:8000
export AWS_REGION_NAME=eu-west-3
export AWS_ACCESS_KEY_ID=fake
export AWS_SECRET_ACCESS_KEY=fake
export DYNAMODB_USERS=phishing-app-dev-users
export DYNAMODB_QUIZZES=phishing-app-dev-quizzes
export DYNAMODB_ATTEMPTS=phishing-app-dev-attempts
export DYNAMODB_RESPONSES=phishing-app-dev-responses
export DYNAMODB_INSPECTOR=phishing-app-dev-inspector-attempts
export S3_BUCKET=phishing-app-dev-local
export SECRET_KEY=dev-secret
python seed_dynamodb.py

# Run the development server
python run.py
```

The app runs on `http://localhost:5000` by default.

**Default admin credentials**: `admin` / `admin123`

## Troubleshooting
- **PEP 668 / externally-managed-environment**: use a venv (`python3 -m venv .venv`).
- **Missing Python deps**: install in venv with `python -m pip install -r requirements.txt`.
- **Lambda plan fails**: build `lambda.zip` with `./scripts/build_lambda.sh`.

## Lambda Packaging

Use the shared build script to create `lambda.zip`:

```bash
./scripts/build_lambda.sh
```

## Make Targets

```bash
make lint
make test
make lambda
```

## CI/CD Variables (GitLab)

Set these in GitLab CI/CD:

- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`
- `TF_ENV` (`dev` or `prod`)
- `TF_VAR_secret_key` (masked)
- `TF_VAR_app_name` (optional, defaults to `phishing-app`)
- `SKIP_SEED` (optional, `true` to skip seeding)

## Session Notes (2026-02-18)
- Dev environment deployed with Terraform (Lambda + API Gateway + DynamoDB + S3).
- Remote state bootstrapped successfully.
- CI/CD fixes: `make` installed in CI, JUnit report enabled, `TF_VAR_secret_key` required.
- CI/CD now auto-deploys dev, manual for prod, and seeds DynamoDB each deploy (skippable via `SKIP_SEED`).
- Added `scripts/import_resources.sh` to import existing AWS resources into state.
- GDPR compliance: analytics/reporting aggregated by class/year/major only.
- Inspector analytics now cohort-based with CSV export.
- Lambda updated to ASGI wrapper (`asgiref` + `mangum`).

## Docker (Local / Production)

```bash
# Build and start (Nginx on port 80 → Gunicorn → Flask)
docker compose up -d --build

# Seed the database
docker compose exec web python seed.py

# View logs
docker compose logs -f

# Stop
docker compose down
```

Access at `http://localhost` (port 80).

## AWS Deployment

See `DEPLOYMENT_GUIDE.md` for the Terraform + GitLab CI/CD deployment workflow.

## Full Project Structure

```
master-Project-Phishing/
├── CLAUDE.md                # THIS FILE — project context for AI assistants
├── README.md                # Repo readme
├── LICENSE                  # CC0 license
├── .gitignore               # Git ignore rules
├── .dockerignore            # Docker build context exclusions
├── Dockerfile               # Flask app container (python:3.12-slim + gunicorn)
├── docker-compose.yml       # Web + Nginx services with SQLite volume
├── requirements.txt         # Python dependencies (Flask, SQLAlchemy, gunicorn, etc.)
├── config.py                # App configuration (SECRET_KEY, DB URI)
├── run.py                   # Entry point — python run.py
├── seed.py                  # Seeds DB with admin user + 10 phishing quiz questions
├── nginx/
│   └── nginx.conf           # Nginx reverse proxy config (port 80 → gunicorn:8000)
├── aws/
│   ├── README.md            # Full AWS Free Tier deployment guide
│   ├── env.example          # Environment variable template for production
│   └── user-data.sh         # EC2 boot script (installs Docker + Compose)
├── app/
│   ├── __init__.py          # Flask app factory (creates app, registers blueprints)
│   ├── models.py            # DynamoDB data access layer (users, quizzes, attempts, responses, inspector attempts)
│   ├── auth/
│   │   ├── __init__.py      # Auth blueprint registration
│   │   ├── routes.py        # Login, register, logout routes
│   │   └── forms.py         # WTForms: LoginForm, RegisterForm
│   ├── quiz/
│   │   ├── __init__.py      # Quiz blueprint registration
│   │   ├── routes.py        # Quiz list, take quiz, submit answers, results, history
│   │   └── forms.py         # WTForms: QuestionForm (radio buttons)
│   ├── dashboard/
│   │   ├── __init__.py      # Dashboard blueprint registration
│   │   └── routes.py        # Admin-only dashboard: stats, charts, recent activity
│   ├── templates/
│   │   ├── base.html        # Base layout: Bootstrap 5 navbar, flash messages
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   ├── quiz/
│   │   │   ├── quiz_list.html
│   │   │   ├── take_quiz.html   # Progress bar, question, explanation after answer
│   │   │   ├── results.html     # Score summary with color-coded feedback
│   │   │   └── history.html     # User's past quiz attempts
│   │   └── dashboard/
│   │       └── dashboard.html   # Admin: stat cards, Chart.js bar chart, tables
│   └── static/
│       └── css/style.css    # Custom styles
│
├── examples/                # Real phishing/spam .eml samples from TryHackMe AOC lab
│   ├── fake-invoice/
│   │   └── fakeinvoice-urgency-spoofing-socialeng.eml
│   ├── impersonation/
│   │   └── impersonation-attachment-socialeng-spoof.eml
│   ├── impersonation-urgency/
│   │   └── impersonation-socialeng-urgency.eml
│   ├── legit-impersonation/
│   │   └── legitapp-impersonation-externaldomain-socialeng.eml
│   ├── punycode/
│   │   └── punycode-impersonation-legitapp-socialeng.eml
│   └── spam/
│       └── marketing-spam-logistics.eml
│
└── Phishing AOC/            # TryHackMe lab reference materials
    ├── AOC Flags & Answers.md           # All 6 email answers, signals, and flags
    ├── Download EML Examples.md         # PowerShell commands to re-download .eml files
    └── email-inspector-source.html      # Source of the TryHackMe email inspector app
```

## Data Models

- **User**: id, username, email, password_hash, is_admin, created_at
- **Quiz**: id, title, description, created_at → has many Questions
- **Question**: id, quiz_id (FK), question_text, explanation → has many Answers
- **Answer**: id, question_id (FK), answer_text, is_correct (boolean)
- **QuizAttempt**: id, user_id (FK), quiz_id (FK), score, total, completed_at

## Features Implemented

### Authentication (`app/auth/`)
- Register / Login / Logout with form validation
- Admin vs regular user roles (is_admin flag)
- Protected routes via Flask-Login `@login_required`

### Phishing Quiz (`app/quiz/`)
- List available quizzes
- Take a quiz: multiple-choice questions with radio buttons
- After each question: show explanation of why it's phishing or legit
- Progress bar during quiz
- Score summary at the end with color-coded feedback
- Quiz history per user

### Admin Dashboard (`app/dashboard/`)
- Admin-only (403 for non-admins)
- Stat cards: total users, total attempts, average score
- Score distribution bar chart (Chart.js) with 5 buckets (0-20%, 20-40%, etc.)
- Per-quiz stats table (average score, completion count)
- Recent activity table (last 10 attempts)

### Seed Data (`seed.py`)
- Creates admin user (admin / admin123)
- Creates 1 quiz with 10 phishing awareness questions covering:
  suspicious URLs, email spoofing, urgency tactics, credential harvesting,
  whaling/CEO fraud, double extensions, smishing, spear phishing, MFA

## Real-World Email Examples (`examples/`)

Six `.eml` files from TryHackMe's Advent of Cyber phishing lab. Each demonstrates different attack techniques:

| Email File | Type | Phishing Signals |
|-----------|------|-----------------|
| `fakeinvoice-urgency-spoofing-socialeng.eml` | Phishing | Fake Invoice, Urgency, Spoofing |
| `impersonation-attachment-socialeng-spoof.eml` | Phishing | Impersonation, Malicious Attachment, Spoofing |
| `impersonation-socialeng-urgency.eml` | Phishing | Impersonation, Social Engineering, Urgency |
| `legitapp-impersonation-externaldomain-socialeng.eml` | Phishing | Impersonation, External Domain, Social Engineering |
| `marketing-spam-logistics.eml` | Spam | N/A |
| `punycode-impersonation-legitapp-socialeng.eml` | Phishing | Punycode/Typosquatting, Impersonation, Social Engineering |

These can be used as teaching material or integrated into the quiz app as real email analysis exercises.

## Phishing Signal Taxonomy

The TryHackMe inspector app uses these 10 signal categories:

| Signal | Description |
|--------|------------|
| Impersonation | Sender pretends to be someone else |
| Typosquatting/Punycodes | Lookalike domains using unicode or typos |
| External Sender Domain | Email from outside the expected organization |
| Spoofing | Forged sender headers |
| Social Engineering Text | Manipulative language to trick the recipient |
| Sense of Urgency | Pressure to act immediately |
| Fake Invoice | Fraudulent billing/payment request |
| Malicious Attachment | Dangerous file attached |
| Fake Login Page | Links to credential harvesting page |
| Side Channel Communication | Asks victim to communicate via alternate channel |

## Potential Next Steps

These are ideas for future development (not yet implemented):

1. **Integrate .eml examples into the app** — Add an "Email Analysis" section where users inspect real `.eml` files and classify them (like the TryHackMe inspector)
2. **EML parser** — Build a Python email parser to extract headers, body, links, and attachments from `.eml` files and display them in the app
3. **More quizzes** — Add quizzes on specific topics (URL analysis, header inspection, social engineering red flags)
4. **User progress tracking** — Show learning progress over time with charts
5. ~~**Docker support**~~ — **DONE**: Dockerfile, docker-compose.yml, Nginx reverse proxy, AWS deployment guide
6. **API endpoints** — REST API for quiz data (useful for mobile app or external integrations)
7. **Email submission** — Let users upload `.eml` files for analysis
8. **Automated scoring** — Use the signal taxonomy to auto-classify uploaded emails

## Important Notes

- The `Phishing AOC/` folder contains TryHackMe CTF flags — these are for educational reference only
- The `.eml` files in `examples/` are real phishing/spam samples — handle with care
- The app uses SQLite (`app.db`) — no external database needed
- All passwords are hashed with Werkzeug (never stored in plaintext)
- The `email-inspector-source.html` in `Phishing AOC/` is the reference UI from TryHackMe's lab that inspired this project
