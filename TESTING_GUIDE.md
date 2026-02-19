# Testing Guide — What to Expect

This guide explains how to test the phishing awareness app at each stage: local development, automated tests, and post-deployment verification.

---
## Quick Runbook

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install pytest moto
make test
make validate-eml
```

## Troubleshooting
- **PEP 668 / externally-managed-environment**: use a venv (`python3 -m venv .venv`).
- **Missing `boto3` or `flask_login`**: ensure deps installed in the venv.
- **Hangs on AWS calls**: tests use `moto`; verify `AWS_*` env vars are set by `tests/conftest.py`.
- **CI artifacts**: `make test` writes `report.xml` for GitLab JUnit reports.


## 1. Running Automated Tests Locally

### Prerequisites

```bash
cd master-Project-Phishing
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install pytest moto
```

### Run All Tests

```bash
pytest tests/ -v
```

### Validate EML Realism

```bash
make validate-eml
```

The report is written to `examples/realism_report.json`. Use `examples/realism_allowlist.json` to skip checks for legacy samples.

### Expected Output

```
tests/test_auth.py::TestLogin::test_login_page_renders PASSED
tests/test_auth.py::TestLogin::test_login_success PASSED
tests/test_auth.py::TestLogin::test_login_wrong_password PASSED
tests/test_auth.py::TestLogin::test_login_nonexistent_user PASSED
tests/test_auth.py::TestLogin::test_logout PASSED
tests/test_auth.py::TestLogin::test_no_register_route PASSED
tests/test_auth.py::TestLogin::test_login_redirects_authenticated PASSED
tests/test_auth.py::TestCSVImport::test_import_requires_admin PASSED
tests/test_auth.py::TestCSVImport::test_import_page_renders_for_admin PASSED
tests/test_auth.py::TestCSVImport::test_import_csv PASSED
tests/test_auth.py::TestCSVImport::test_import_csv_skips_existing PASSED
tests/test_auth.py::TestCSVImport::test_import_csv_missing_columns PASSED
tests/test_models.py::TestUserModel::test_create_and_get_user PASSED
tests/test_models.py::TestUserModel::test_get_user_not_found PASSED
tests/test_models.py::TestUserModel::test_get_user_by_email PASSED
tests/test_models.py::TestUserModel::test_batch_create_users PASSED
tests/test_models.py::TestUserModel::test_batch_create_users_skips_existing PASSED
tests/test_models.py::TestUserModel::test_list_users_by_group PASSED
tests/test_models.py::TestUserModel::test_count_users PASSED
tests/test_models.py::TestUserModel::test_get_distinct_groups PASSED
tests/test_models.py::TestQuizModel::test_create_and_get_quiz PASSED
tests/test_models.py::TestQuizModel::test_list_quizzes PASSED
tests/test_models.py::TestAttemptModel::test_create_and_get_attempt PASSED
tests/test_models.py::TestAttemptModel::test_one_attempt_per_user_per_quiz PASSED
tests/test_models.py::TestAttemptModel::test_list_attempts_by_user PASSED
tests/test_models.py::TestAttemptModel::test_list_attempts_by_group PASSED
tests/test_models.py::TestResponseModel::test_save_and_get_responses PASSED
tests/test_models.py::TestResponseModel::test_get_responses_by_question PASSED
tests/test_quiz.py::TestQuizList::test_quiz_list_requires_login PASSED
tests/test_quiz.py::TestQuizList::test_quiz_list_shows_quizzes PASSED
tests/test_quiz.py::TestQuizList::test_quiz_list_shows_completed_badge PASSED
tests/test_quiz.py::TestQuizLock::test_start_quiz_redirects_if_already_completed PASSED
tests/test_quiz.py::TestQuizLock::test_start_quiz_works_for_new_attempt PASSED
tests/test_quiz.py::TestTakeQuiz::test_take_question_renders PASSED
tests/test_quiz.py::TestTakeQuiz::test_submit_answer_saves_response PASSED
tests/test_quiz.py::TestQuizHistory::test_history_shows_attempts PASSED
tests/test_quiz.py::TestQuizHistory::test_history_empty PASSED

========================= 36 passed in X.XXs =========================
```

### What the Tests Cover

| Test File | What It Tests |
|-----------|--------------|
| `test_models.py` | DynamoDB data access layer — CRUD for users, quizzes, attempts, responses; batch import; one-attempt enforcement |
| `test_auth.py` | Login/logout flow, register route removed (404), CSV import (admin only, valid CSV, missing columns, duplicate skip) |
| `test_quiz.py` | Quiz list rendering, completed badge, quiz lock (redirect if already done), answer submission saves responses, history |

### How Tests Work

- Tests use **moto** to mock AWS services — no real AWS calls are made
- Each test gets a fresh set of DynamoDB tables and S3 bucket
- CSRF is disabled in tests (`WTF_CSRF_ENABLED = False`)
- Helper fixtures (`seed_admin`, `seed_user`, `seed_quiz`) create test data

---

## 2. Local Development Testing with DynamoDB Local

You can run the full app locally using DynamoDB Local (Docker):

### 2.1 Start DynamoDB Local

```bash
docker run -d -p 8000:8000 amazon/dynamodb-local
```

### 2.2 Create Tables Locally

```bash
# Set environment for local development
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

# Create tables using AWS CLI pointed at local DynamoDB
aws dynamodb create-table \
  --endpoint-url http://localhost:8000 \
  --table-name phishing-app-dev-users \
  --key-schema AttributeName=username,KeyType=HASH \
  --attribute-definitions \
    AttributeName=username,AttributeType=S \
    AttributeName=email,AttributeType=S \
    AttributeName=group,AttributeType=S \
  --global-secondary-indexes \
    '[{"IndexName":"email-index","KeySchema":[{"AttributeName":"email","KeyType":"HASH"}],"Projection":{"ProjectionType":"ALL"}},{"IndexName":"group-index","KeySchema":[{"AttributeName":"group","KeyType":"HASH"},{"AttributeName":"username","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}}]' \
  --billing-mode PAY_PER_REQUEST

aws dynamodb create-table \
  --endpoint-url http://localhost:8000 \
  --table-name phishing-app-dev-quizzes \
  --key-schema AttributeName=quiz_id,KeyType=HASH \
  --attribute-definitions AttributeName=quiz_id,AttributeType=S \
  --billing-mode PAY_PER_REQUEST

aws dynamodb create-table \
  --endpoint-url http://localhost:8000 \
  --table-name phishing-app-dev-attempts \
  --key-schema AttributeName=username,KeyType=HASH AttributeName=quiz_id,KeyType=RANGE \
  --attribute-definitions \
    AttributeName=username,AttributeType=S \
    AttributeName=quiz_id,AttributeType=S \
    AttributeName=completed_at,AttributeType=S \
    AttributeName=group,AttributeType=S \
  --global-secondary-indexes \
    '[{"IndexName":"quiz-index","KeySchema":[{"AttributeName":"quiz_id","KeyType":"HASH"},{"AttributeName":"completed_at","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}},{"IndexName":"group-index","KeySchema":[{"AttributeName":"group","KeyType":"HASH"},{"AttributeName":"completed_at","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}}]' \
  --billing-mode PAY_PER_REQUEST

aws dynamodb create-table \
  --endpoint-url http://localhost:8000 \
  --table-name phishing-app-dev-responses \
  --key-schema AttributeName=username_quiz_id,KeyType=HASH AttributeName=question_id,KeyType=RANGE \
  --attribute-definitions \
    AttributeName=username_quiz_id,AttributeType=S \
    AttributeName=question_id,AttributeType=S \
    AttributeName=quiz_question_id,AttributeType=S \
    AttributeName=username,AttributeType=S \
  --global-secondary-indexes \
    '[{"IndexName":"quiz-question-index","KeySchema":[{"AttributeName":"quiz_question_id","KeyType":"HASH"},{"AttributeName":"username","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}}]' \
  --billing-mode PAY_PER_REQUEST

aws dynamodb create-table \
  --endpoint-url http://localhost:8000 \
  --table-name phishing-app-dev-inspector-attempts \
  --key-schema AttributeName=username,KeyType=HASH AttributeName=submitted_at,KeyType=RANGE \
  --attribute-definitions \
    AttributeName=username,AttributeType=S \
    AttributeName=submitted_at,AttributeType=S \
    AttributeName=group,AttributeType=S \
    AttributeName=email_file,AttributeType=S \
  --global-secondary-indexes \
    '[{"IndexName":"group-index","KeySchema":[{"AttributeName":"group","KeyType":"HASH"},{"AttributeName":"submitted_at","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}},{"IndexName":"email-index","KeySchema":[{"AttributeName":"email_file","KeyType":"HASH"},{"AttributeName":"submitted_at","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}}]' \
  --billing-mode PAY_PER_REQUEST
```

### 2.3 Seed and Run

```bash
python seed_dynamodb.py
python run.py
```

Visit `http://localhost:5000`. The app works identically to the Lambda version, except:
- EML files in the inspector won't load (they'd need S3/LocalStack)
- Report downloads won't work without S3

### 2.4 Optional: Full local stack with LocalStack

For full S3 support locally, use LocalStack:

```bash
docker run -d -p 4566:4566 localstack/localstack

export S3_ENDPOINT=http://localhost:4566
aws --endpoint-url http://localhost:4566 s3 mb s3://phishing-app-dev-local
aws --endpoint-url http://localhost:4566 s3 sync examples/ s3://phishing-app-dev-local/eml-samples/
```

---

## 3. Post-Deployment Verification Checklist

After deploying to AWS, run through this checklist manually:

### 3.1 Basic Access

| Step | Expected Result |
|------|----------------|
| Visit API Gateway URL | Login page loads with "Phishing Awareness" navbar |
| Check for HTTPS | URL starts with `https://` |
| Check page load time | < 3 seconds (Lambda cold start may be up to 5s first time) |

### 3.2 Authentication

| Step | Expected Result |
|------|----------------|
| Login as `admin` / `admin123` | Redirected to quiz list, "Logged in successfully" flash |
| Try to access `/auth/register` | 404 Not Found |
| Logout | Redirected to login, "You have been logged out" flash |
| Try wrong password | "Invalid username or password" flash |

### 3.3 CSV User Import

| Step | Expected Result |
|------|----------------|
| Login as admin | Works |
| Click Admin → Import Users | CSV upload form loads |
| Upload a valid CSV | "Imported N users" success message with count |
| Upload same CSV again | "N skipped (already exist)" message |
| Upload CSV missing columns | "CSV must contain columns" error |
| Login as imported user | Works with the password from CSV |

**Sample test CSV:**
```csv
username,email,password,group
testuser1,test1@company.com,TempPass1,engineering
testuser2,test2@company.com,TempPass2,marketing
testuser3,test3@company.com,TempPass3,engineering
```

### 3.4 Quiz Flow (One-Attempt Lock)

| Step | Expected Result |
|------|----------------|
| Login as a regular user | Quiz list shows available quizzes |
| Click "Start Quiz" | Training video page loads with Start disabled |
| Finish the video | Start Quiz becomes enabled |
| Click "Start Quiz" | First question loads with progress bar |
| Answer a question | Correct/Incorrect feedback + explanation shown |
| Complete all questions | Results page with score and percentage |
| Go back to quiz list | Quiz shows green "Completed" badge, button says "Already Completed" |
| Try to start same quiz again | Redirected to results with "already completed" message |
| Check My History | Shows single attempt with score and date |

### 3.5 Admin Dashboard

| Step | Expected Result |
|------|----------------|
| Login as admin | Dashboard shows stat cards |
| Check stat cards | Total Users, Completed, Pending, Average Score all show numbers |
| Score Distribution chart | Bar chart with 5 buckets renders |
| Group Comparison chart | Bar chart showing average per group |
| Per-Quiz Stats table | Shows quiz title, attempt count, average |
| Group Statistics table | Shows group name, attempt count, average |
| Recent Activity table | Last 10 attempts with user, quiz, score, date |
| Wait 30 seconds | Stat cards update automatically (live polling) |

### 3.6 Reports

| Step | Expected Result |
|------|----------------|
| Admin → Reports | Report options form loads |
| Select "Summary" + Generate | Spinner → "Report Ready" card with download link |
| Click Download | CSV file downloads with group averages |
| Select "Detailed" + Generate | CSV file downloads with per-user scores |
| Download link | Works for 1 hour, then expires |

### 3.7 Email Inspector

| Step | Expected Result |
|------|----------------|
| Click "Email Inspector" in nav | Inspector page loads |
| Email list loads | Shows 6 .eml files from S3 |
| Click an email | Full detail view: headers, body, links, attachments, warnings |
| Check warnings | Punycode, spoofing, suspicious URL warnings appear where expected |

### 3.8 Non-Admin Restrictions

| Step | Expected Result |
|------|----------------|
| Login as regular user | No "Admin" dropdown in navbar |
| Visit `/dashboard/` directly | 403 Forbidden |
| Visit `/auth/admin/import-users` directly | 403 Forbidden |
| Visit `/dashboard/reports` directly | 403 Forbidden |

---

## 4. Manual Feature Tests (Detailed)

Use these steps to create and verify the tests you listed. Capture screenshots and logs if something fails.

### 4.1 Users Upload (CSV Import)

1. Login as `admin` / `admin123`.
2. Navigate to Admin → Import Users.
3. Upload a CSV with at least 3 users. Use the sample below.
4. Verify the success banner shows imported count.
5. Try uploading the same CSV again and confirm the "skipped" count.
6. Log out and log in as one imported user to verify credentials.

**Sample CSV**
```csv
username,email,password,group
testuser1,test1@company.com,TempPass1,engineering
testuser2,test2@company.com,TempPass2,marketing
testuser3,test3@company.com,TempPass3,engineering
```

**Expected**
- Import success message with correct count.
- Second import shows skipped users.
- Imported users can log in.

### 4.2 Mails Upload (EML Samples to S3)

1. Upload `.eml` files to `s3://<bucket>/eml-samples/` (already done in deploy jobs).
2. Open Email Inspector in the app.
3. Confirm the email list loads and includes the uploaded files.
4. Click a file and verify details render.

**Expected**
- 6 example emails are listed.
- Email detail view shows headers, HTML/text body, links, and warnings.

### 4.3 Answer Verification (Quiz Submissions)

1. Log in as a non-admin user.
2. Start a quiz and answer all questions.
3. Verify correctness feedback appears after each question.
4. Finish the quiz and record the final score.
5. Re-open the quiz list and confirm the completed state.

**Expected**
- Each submitted answer shows correct/incorrect feedback.
- Final score matches the number of correct answers.
- The quiz is locked after completion.

### 4.4 Analytics (Dashboard and Inspector)

1. Log in as admin and open the dashboard.
2. Verify Total Users, Completed, Pending, and Average Score show correct values.
3. Confirm the score distribution and per-quiz stats match the attempts you created.
4. Open the Inspector analytics page and confirm it shows attempts per cohort.
5. Apply filters (class/year/major/email) and verify the table updates.

**Expected**
- Counts align with actual attempts.
- Filters narrow the data correctly.

### 4.5 Reports (CSV Generation)

1. Log in as admin and open Reports.
2. Generate Summary and Detailed reports.
3. Download each CSV and verify content.
4. Generate Inspector report and verify cohort counts and correct percentage.

**Expected**
- CSV downloads work and match the dashboard data.
- Presigned links are valid for 1 hour.

### 4.6 Authentication: Change Password

1. Log in as a regular user.
2. Navigate to the profile or change-password screen if available.
3. Change the password and log out.
4. Log in with the new password.
5. Verify the old password no longer works.

**Expected**
- Password change succeeds and persists.
- Old password fails.
- New password works.

### 4.7 Inspector Lockout Flow

1. Login as a regular user and open the Inspector.
2. Submit answers for all 8 assigned emails.
3. After the last submission, verify a completion message appears.
4. Refresh the Inspector page.
5. Confirm the Inspector is blocked and shows the completion message.
6. As admin, go to **Admin → Inspector Analytics** and reset the user.
7. Log back in as the user and verify Inspector access is restored.

Optional: Use the bulk reset buttons to reset the current cohort filters or all users.

**Expected**
- Each email can be submitted only once.
- After 8 submissions, the Inspector is locked.
- Admin reset restores access.

### 4.7 Test Run Checklist Template

Use this template to record results for a test session.

```text
Test Run Date:
Environment (local/dev/prod):
App URL:
Commit Hash:
Tester:

Users Upload (CSV Import)
- Status (Pass/Fail):
- Notes:

Mails Upload (EML to S3)
- Status (Pass/Fail):
- Notes:

Answer Verification (Quiz Submissions)
- Status (Pass/Fail):
- Notes:

Analytics (Dashboard + Inspector)
- Status (Pass/Fail):
- Notes:

Reports (Summary/Detailed/Inspector)
- Status (Pass/Fail):
- Notes:

Authentication: Change Password
- Status (Pass/Fail):
- Notes:
```

---

## 5. GitLab Pipeline Verification

When you push to GitLab, check each stage:

### Stage: lint
- **Pass**: No flake8 errors
- **Fail**: Fix the reported style issues (line too long, unused import, etc.)

### Stage: test
- **Pass**: All 36 tests pass
- **Fail**: Read the test output — it shows which test failed and why

### Stage: build
- **Pass**: `lambda.zip` artifact is created (visible in job artifacts)
- **Fail**: Usually a `pip install` or `zip` issue

### Stage: plan
- **Pass**: Review the plan output in the job log. It shows what Terraform will create:
  - `Plan: 15 to add, 0 to change, 0 to destroy` (first deploy)
  - Subsequent deploys show only changes
- **Fail**: Terraform configuration error — check `.tf` files

### Stage: deploy
- **Manual trigger**: Click the play button on the deploy job
- **Pass**: Terraform apply completes, EML files uploaded to S3
- **Fail**: Check Terraform error message (usually permissions or resource conflicts)

---

## 5. Quick Smoke Test Script

After deployment, run this quick check from your terminal:

```bash
# Set your API Gateway URL
API_URL="https://your-api-id.execute-api.eu-west-3.amazonaws.com"

# 1. Check the app is running (should return HTML with "Login")
curl -s "$API_URL/auth/login" | grep -o "Login"

# 2. Check API endpoints exist
curl -s -o /dev/null -w "%{http_code}" "$API_URL/inspector/api/emails"
# Expected: 200

# 3. Check non-existent route
curl -s -o /dev/null -w "%{http_code}" "$API_URL/nonexistent"
# Expected: 404

# 4. Check unauthenticated access to quiz
curl -s -o /dev/null -w "%{http_code}" "$API_URL/quiz/"
# Expected: 302 (redirect to login)
```

---

## 6. Monitoring After Deployment

### CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/phishing-app-prod-app --follow

# View API Gateway logs
aws logs tail /aws/apigateway/phishing-app-prod-api --follow
```

### DynamoDB Data Check

```bash
# Count users
aws dynamodb scan --table-name phishing-app-prod-users --select COUNT

# List all quizzes
aws dynamodb scan --table-name phishing-app-prod-quizzes \
  --projection-expression "quiz_id, title"

# Count attempts
aws dynamodb scan --table-name phishing-app-prod-attempts --select COUNT
```

### S3 Content Check

```bash
# List EML files
aws s3 ls s3://phishing-app-prod-eu-west-3/eml-samples/

# List generated reports
aws s3 ls s3://phishing-app-prod-eu-west-3/reports/
```
