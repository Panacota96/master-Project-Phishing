# Local Development Setup — Phishing Awareness Training

## Prerequisites

- **Python 3.12+**
- **Docker + Docker Compose** (for DynamoDB Local and Option A)
- **Make** (optional, simplifies commands)

---

## Option A — Docker Compose (Recommended)

The `docker-compose.yml` includes three services: `dynamodb-local` (port 8766), `web` (Gunicorn/Flask), and `nginx` (port 80).

```bash
# 1. Clone and enter the repo
git clone <repository-url>
cd master-Project-Phishing

# 2. Copy the env file (already present in the repo)
cp .env.example .env   # edit SECRET_KEY and other vars as needed

# 3. Start all services
docker compose up -d --build

# 4. Create DynamoDB tables
python setup_local_db.py   # hits http://localhost:8766 directly

# 5. Seed admin user + quizzes
docker compose exec web python seed_dynamodb.py
```

Access at **http://localhost** (port 80). Default admin: `admin` / `admin123`.

---

## Option B — Standalone DynamoDB Local + `python run.py`

Use this option when you want to run Flask directly without Docker Compose (faster iteration).

### Step 1: Clone and create a virtual environment

```bash
git clone <repository-url>
cd master-Project-Phishing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Start DynamoDB Local

```bash
docker run -d -p 8766:8000 amazon/dynamodb-local
```

### Step 3: Export environment variables

```bash
# AWS / DynamoDB Local
export AWS_REGION_NAME=eu-west-3
export AWS_ACCESS_KEY_ID=fake
export AWS_SECRET_ACCESS_KEY=fake
export DYNAMODB_ENDPOINT=http://localhost:8766

# DynamoDB Table Names
export DYNAMODB_USERS=phishing-app-dev-users
export DYNAMODB_QUIZZES=phishing-app-dev-quizzes
export DYNAMODB_ATTEMPTS=phishing-app-dev-attempts
export DYNAMODB_RESPONSES=phishing-app-dev-responses
export DYNAMODB_INSPECTOR=phishing-app-dev-inspector-attempts
export DYNAMODB_INSPECTOR_ANON=phishing-app-dev-inspector-attempts-anon
export DYNAMODB_BUGS=phishing-app-dev-bugs
export DYNAMODB_ANSWER_KEY_OVERRIDES=phishing-app-dev-answer-key-overrides
export DYNAMODB_COHORT_TOKENS=phishing-app-dev-cohort-tokens

# Storage
export S3_BUCKET=phishing-app-dev-eu-west-3
export SECRET_KEY=dev-secret-key

# Registration worker (leave blank for local dev — SQS not needed)
export SQS_REGISTRATION_QUEUE_URL=
export SES_FROM_EMAIL=no-reply@example.com
```

### Step 4: Create tables and seed the database

```bash
python setup_local_db.py   # creates all DynamoDB tables
python seed_dynamodb.py    # seeds admin user + quizzes
```

### Step 5: Run the app

```bash
python run.py
```

Visit **http://localhost:5000**. Default admin: `admin` / `admin123`.

---

## All Environment Variables Reference

| Variable | Local dev value | Purpose |
|---|---|---|
| `AWS_REGION_NAME` | `eu-west-3` | AWS region |
| `AWS_ACCESS_KEY_ID` | `fake` | DynamoDB Local auth |
| `AWS_SECRET_ACCESS_KEY` | `fake` | DynamoDB Local auth |
| `DYNAMODB_ENDPOINT` | `http://localhost:8766` | Points to local DynamoDB |
| `DYNAMODB_USERS` | `phishing-app-dev-users` | Users table |
| `DYNAMODB_QUIZZES` | `phishing-app-dev-quizzes` | Quiz definitions |
| `DYNAMODB_ATTEMPTS` | `phishing-app-dev-attempts` | Quiz scores |
| `DYNAMODB_RESPONSES` | `phishing-app-dev-responses` | Per-question answers |
| `DYNAMODB_INSPECTOR` | `phishing-app-dev-inspector-attempts` | Inspector attempts (auth) |
| `DYNAMODB_INSPECTOR_ANON` | `phishing-app-dev-inspector-attempts-anon` | Anonymous inspector attempts (GDPR) |
| `DYNAMODB_BUGS` | `phishing-app-dev-bugs` | Bug reports |
| `DYNAMODB_ANSWER_KEY_OVERRIDES` | `phishing-app-dev-answer-key-overrides` | Admin answer key overrides |
| `DYNAMODB_COHORT_TOKENS` | `phishing-app-dev-cohort-tokens` | QR registration tokens |
| `S3_BUCKET` | `phishing-app-dev-eu-west-3` | S3 bucket name |
| `SECRET_KEY` | `dev-secret-key` | Flask session signing key |
| `SQS_REGISTRATION_QUEUE_URL` | *(leave empty locally)* | SQS queue for self-registration |
| `SES_FROM_EMAIL` | `no-reply@example.com` | Confirmation email sender |

---

## Developer Toolbox

```bash
make lint           # flake8 --max-line-length=120
make test           # pytest + moto (no real AWS needed)
make validate-eml   # validate EML realism scores
make lambda         # build lambda.zip
```
