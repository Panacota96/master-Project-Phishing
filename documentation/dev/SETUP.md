# Local Development Setup - Phishing Awareness Training

## Prerequisites
- **Python 3.12+**
- **Docker** (for DynamoDB Local)
- **Make** (optional, but simplifies commands)

## Step 1: Clone and Environment
```bash
git clone <repository-url>
cd master-Project-Phishing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Database (Local)
Start DynamoDB Local:
```bash
docker run -d -p 8000:8000 amazon/dynamodb-local
```

## Step 3: Environment Configuration
Create a `.env` file or export these variables for your local session:

```bash
# AWS / DynamoDB Local
export AWS_REGION_NAME=eu-west-3
export AWS_ACCESS_KEY_ID=fake
export AWS_SECRET_ACCESS_KEY=fake
export DYNAMODB_ENDPOINT=http://localhost:8000

# Table Names (matches seed_dynamodb.py)
export DYNAMODB_USERS=phishing-app-dev-users
export DYNAMODB_QUIZZES=phishing-app-dev-quizzes
export DYNAMODB_ATTEMPTS=phishing-app-dev-attempts
export DYNAMODB_RESPONSES=phishing-app-dev-responses
export DYNAMODB_INSPECTOR=phishing-app-dev-inspector-attempts
export DYNAMODB_INSPECTOR_ANON=phishing-app-dev-inspector-attempts-anon
export DYNAMODB_BUGS=phishing-app-dev-bugs
export DYNAMODB_ANSWER_KEY_OVERRIDES=phishing-app-dev-answer-key-overrides

# Storage
export S3_BUCKET=phishing-app-dev
export SECRET_KEY=dev-secret-key
```

## Step 4: Seeding the Database
```bash
python seed_dynamodb.py
```

## Step 5: Run the App
```bash
python run.py
```
Visit **http://localhost:5000**. Default admin: `admin` / `admin123`.

## Developer Toolbox
- **Linting**: `make lint`
- **Testing**: `make test`
- **EML Realism Check**: `make validate-eml`
- **Build Lambda**: `./scripts/build_lambda.sh`
