# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Phishing awareness training web application (Flask + AWS Serverless + Terraform) for ESME engineering school. Users take interactive quizzes on phishing techniques and analyze real `.eml` files in the Email Threat Inspector.

## Commands

```bash
# Run locally (port 5000)
python run.py

# Test (uses pytest + moto for mocked AWS)
make test

# Run a single test file
pytest tests/test_inspector.py -v

# Lint (flake8, max-line-length=120)
make lint

# Build Lambda artifact
make lambda                    # ./scripts/build_lambda.sh

# Validate .eml realism
make validate-eml

# Sync video assets to S3
make sync-assets
```

### Local Development with DynamoDB Local

**Option A — Docker Compose (recommended):** The `docker-compose.yml` includes a `dynamodb-local` service (exposes port `8766` to the host). Copy `.env` (already present) and start everything, then create tables:

```bash
docker compose up -d --build
python setup_local_db.py   # creates DynamoDB tables directly via boto3
python seed_dynamodb.py    # seeds admin user + quizzes via Flask app context
```

`setup_local_db.py` hits `http://localhost:8766` by default; `seed_dynamodb.py` reads the env vars below.

**Option B — Standalone DynamoDB Local + `python run.py`:**

```bash
docker run -d -p 8766:8000 amazon/dynamodb-local
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
export S3_BUCKET=phishing-app-dev-eu-west-3
export SECRET_KEY=dev-secret
export SQS_REGISTRATION_QUEUE_URL=
export SES_FROM_EMAIL=no-reply@example.com
# Optional: Microsoft 365 SSO (leave empty to disable)
export MSAL_CLIENT_ID=
export MSAL_CLIENT_SECRET=
export MSAL_AUTHORITY=https://login.microsoftonline.com/common/v2.0
export MSAL_ADMIN_GROUP_ID=
python seed_dynamodb.py
```

## Architecture

### App Factory & Blueprints

`app/__init__.py` creates the Flask app via `create_app()`, initializes `boto3` DynamoDB resource and S3 client on `app.dynamodb` / `app.s3_client`, then registers four blueprints:

| Blueprint | Prefix | Purpose |
|-----------|--------|---------|
| `app/auth` | `/auth` | Login, register, logout (Flask-Login + Werkzeug hashing) |
| `app/quiz` | `/quiz` | Quiz list, video gate, take quiz, results, history |
| `app/dashboard` | `/dashboard` | Admin stats, analytics, bug reports, user management |
| `app/inspector` | `/inspector` | Email Threat Inspector (EML parsing + JSON API) |

### Data Access Layer

ALL DynamoDB access goes through `app/models.py` — never use `boto3` directly in routes. Tables are referenced by config key via `_get_table(name_config_key)`.

DynamoDB tables (configured via env vars, keys defined in `config.py`):
- `DYNAMODB_USERS` — users with cohort fields (class_name, academic_year, major, group); GSI on `email` and `group`
- `DYNAMODB_QUIZZES` — quiz definitions with embedded questions array
- `DYNAMODB_ATTEMPTS` — quiz scores, one per user per quiz (enforced by condition expression); GSI on `quiz_id` and `group`
- `DYNAMODB_RESPONSES` — per-question answers; composite key `username_quiz_id#question_id`; GSI on `quiz_question_id`
- `DYNAMODB_INSPECTOR` — inspector submissions with cohort fields; GSI on `group` and `email_file`
- `DYNAMODB_INSPECTOR_ANON` — GDPR-safe anonymous inspector attempts (no username)
- `DYNAMODB_BUGS` — bug reports with status field
- `DYNAMODB_ANSWER_KEY_OVERRIDES` — admin-editable overrides for email classifications and required signals; takes precedence over the static `ANSWER_KEY` dict at runtime via `get_effective_answer_key()`

### Inspector Flow

The Email Threat Inspector (`app/inspector/routes.py`) works as a JSON API consumed by a JavaScript front-end:
1. EML files are stored in S3 under `eml-samples/` prefix
2. `api_email_list` → builds a per-session pool of up to 8 emails (1–3 spam, rest phishing) from files that exist in both S3 and `ANSWER_KEY`
3. `api_email_detail` → parses EML (stdlib `email` module) or JSON-formatted EML; cleans template placeholders via `_clean_placeholders()`
4. `api_submit` → validates classification + exactly N signals for Phishing (N = `len(entry['signals'])` from the effective answer key; 0 for Spam), checks against the effective answer key, writes to anonymous table, locks user after all 8 submitted
5. Ground truths live in `app/inspector/answer_key.py` (`ANSWER_KEY` dict keyed by filename); admins can override per-email via `DYNAMODB_ANSWER_KEY_OVERRIDES` table — overrides win at runtime via `get_effective_answer_key()` in `app/models.py`

### Quiz Flow

Quizzes require watching a training video before starting (enforced via `session['quiz_video_watched']`). One attempt per user per quiz is enforced by a DynamoDB conditional `put_item`. Quiz data (questions, video URLs) is seeded via `seed_dynamodb.py`.

### Testing

> **No self-registration**: there is no public registration flow. All user accounts are created by admins — either manually or via the CSV bulk-import endpoint (`/auth/admin/import-users`). When writing tests that need a student user, use the `seed_user` fixture from `conftest.py` rather than simulating a registration form.

Tests use `moto` to mock all AWS services. The `conftest.py` fixture `app()` wraps everything in `mock_aws()`, creates all DynamoDB tables with correct schemas and GSIs, and creates an S3 bucket. CSRF is disabled in tests. Use `seed_admin`, `seed_user`, `seed_quiz` fixtures and the `login()` helper in `conftest.py`.

### Deployment

- **Lambda**: Flask is wrapped with `mangum` for AWS Lambda + API Gateway
- **Terraform**: `terraform/` manages all AWS infrastructure; `terraform/bootstrap/` creates the Terraform state bucket
- **CI/CD**: GitHub Actions — four workflows: `ci.yml` (lint/test/build), `deploy-dev.yml` (auto-deploy on push to main), `deploy-prod.yml` (manual), `destroy.yml` (manual teardown); plus `claude.yml` and `claude-code-review.yml`. Uses OIDC to assume the deploy role — no static AWS keys stored in GitHub secrets.
- **Docker**: `docker compose up -d --build` starts three services: `dynamodb-local` (port 8766), `web` (Gunicorn/Flask, reads `.env`), and `nginx` (port 80). Static assets are served directly by Nginx; app routes go through the reverse proxy to Gunicorn.

## Code Conventions

- **Models only**: never call `current_app.dynamodb` directly from routes; use `app/models.py` functions
- **Blueprints**: each blueprint has its own `__init__.py`, `routes.py`, and optionally `forms.py`
- **Config**: all settings read from environment variables in `config.py`; never hardcode table names
- **MIME**: all `.eml` samples must use `multipart/alternative` structure for consistent parsing
- **EML answer key**: when adding new `.eml` files to S3, add corresponding entries to `app/inspector/answer_key.py`; files without an entry are excluded from the inspector pool
- **Phishing signals** (normalized lowercase, alphanumeric): `impersonation`, `punycode`, `externaldomain`, `spoof`, `socialeng`, `urgency`, `fakeinvoice`, `attachment`, `fakelogin`, `sidechannel`

## Known Gotchas

- **CSV import requires `facility`**: The user import CSV (`/auth/admin/import-users`) requires `facility` as a mandatory column alongside `username`, `email`, `password`, `class`, `academic_year`, `major`. Tests that build CSV fixtures must include this column or the route returns a validation error instead of importing.
- **Answer key overrides table**: Any new environment (local dev, test, prod) needs `DYNAMODB_ANSWER_KEY_OVERRIDES` set. Tests use `test-answer-key-overrides`; local dev uses `phishing-app-dev-answer-key-overrides`.
- **Inspector signal count is dynamic**: `api_submit` and the student JS both derive the required signal count from `len(requirement['signals'])`, not from a hardcoded `3`. When editing the answer key (static or via override), the signal list length drives validation on both client and server.

## Documentation Updates (after major implementations)

After completing any major implementation (new feature, infrastructure change, schema change, new flow, significant refactor), always update:

1. **`documentation/ARCHITECTURE.md`** — update or add the relevant Mermaid diagram(s) to reflect the new components, flows, or data model
2. **`CHANGELOG.md`** (if present) — add an entry under the current date describing what changed
3. **`README.md`** — update any section that references the changed functionality (setup steps, feature list, environment variables, etc.)
4. **`documentation/REQUIREMENTS.md`** — update if the change affects functional or non-functional requirements

Minor fixes (typos, lint, single-line patches, doc-only edits) do not require documentation updates.

---

## Hooks (automated checks)

Project-level hooks are configured in `.claude/settings.json` and run automatically after every file edit:

- **`validate-python.sh`** — runs `python3 -m py_compile` on any `.py` file after Edit/Write; exits 2 (blocking) on syntax error so Claude fixes immediately
- **`validate-answer-key.sh`** — validates that every `ANSWER_KEY` entry in `answer_key.py` has `classification` and `signals` keys after the file is edited
