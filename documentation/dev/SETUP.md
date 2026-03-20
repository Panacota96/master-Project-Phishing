# Local Development Setup - En Garde

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
docker run -d -p 8766:8000 amazon/dynamodb-local
```

## Step 3: Environment Configuration
Create a `.env` file or export these variables for your local session:

```bash
# AWS / DynamoDB Local
export AWS_REGION_NAME=eu-west-3
export AWS_ACCESS_KEY_ID=fake
export AWS_SECRET_ACCESS_KEY=fake
export DYNAMODB_ENDPOINT=http://localhost:8766

# Table Names (matches seed_dynamodb.py)
export DYNAMODB_USERS=en-garde-dev-users
export DYNAMODB_QUIZZES=en-garde-dev-quizzes
export DYNAMODB_ATTEMPTS=en-garde-dev-attempts
export DYNAMODB_RESPONSES=en-garde-dev-responses
export DYNAMODB_INSPECTOR=en-garde-dev-inspector-attempts
export DYNAMODB_INSPECTOR_ANON=en-garde-dev-inspector-attempts-anon
export DYNAMODB_BUGS=en-garde-dev-bugs
export DYNAMODB_ANSWER_KEY_OVERRIDES=en-garde-dev-answer-key-overrides

# Storage
export S3_BUCKET=en-garde-dev
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
