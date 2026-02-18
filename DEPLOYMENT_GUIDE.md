# Deployment Guide — Serverless AWS (Terraform + GitLab CI/CD)

This guide explains how to deploy the phishing awareness app to AWS using Terraform and GitLab CI/CD.

---
## Quick Runbook (Dev)

Short path for a dev deployment:

```bash
# Create and activate venv (required on PEP 668 systems)
python3 -m venv .venv
source .venv/bin/activate

# Build Lambda
./scripts/build_lambda.sh

# Terraform init (dev backend)
cd terraform
terraform init -backend-config=backend/dev.hcl

# Configure variables
cp env/dev.tfvars.example env/dev.tfvars
# edit env/dev.tfvars

# Plan + apply
terraform plan -var-file=env/dev.tfvars
terraform apply -var-file=env/dev.tfvars

# Upload EML samples
aws s3 sync ../examples/ s3://<dev-bucket>/eml-samples/ --exclude "*" --include "*.eml"

# Seed data
export AWS_REGION_NAME=<region>
export DYNAMODB_USERS=<dev-users-table>
export DYNAMODB_QUIZZES=<dev-quizzes-table>
export DYNAMODB_ATTEMPTS=<dev-attempts-table>
export DYNAMODB_RESPONSES=<dev-responses-table>
export DYNAMODB_INSPECTOR=<dev-inspector-table>
export S3_BUCKET=<dev-bucket>
export SECRET_KEY=<same-secret-as-terraform>
python seed_dynamodb.py
```

## Troubleshooting
- **`terraform plan` fails with missing `lambda.zip`**: run `./scripts/build_lambda.sh`.
- **AccessDenied for DynamoDB**: switch to `terraform-deployer` or update IAM permissions.
- **PEP 668 / pip install blocked**: use a venv (`python3 -m venv .venv`).
- **Wrong bucket/env**: ensure `<env>` placeholders are replaced (dev vs prod).

## Session Log (Example — Dev)
Use this as a template to document what was done in this session.

**Bootstrap remote state (completed)**  
- `terraform/bootstrap`  
- S3 state bucket created: `phishing-terraform-state`  
- DynamoDB lock table created: `phishing-terraform-locks`  

**Terraform dev apply (completed)**  
- API Gateway URL: `https://xfwnu5ncf9.execute-api.eu-west-3.amazonaws.com`  
- DynamoDB tables:  
  - `phishing-app-dev-users`  
  - `phishing-app-dev-quizzes`  
  - `phishing-app-dev-attempts`  
  - `phishing-app-dev-responses`  
  - `phishing-app-dev-inspector-attempts`  
- S3 bucket: `phishing-app-dev-eu-west-3`  
- Lambda function: `phishing-app-dev-app`  

## Next Steps (to finish the dev deploy)
1. Upload EML samples to S3:
   ```bash
   aws s3 sync ../examples/ s3://phishing-app-dev-eu-west-3/eml-samples/ --exclude "*" --include "*.eml"
   ```
2. Seed DynamoDB with admin user and quiz content:
   ```bash
   export AWS_REGION_NAME=eu-west-3
   export DYNAMODB_USERS=phishing-app-dev-users
   export DYNAMODB_QUIZZES=phishing-app-dev-quizzes
   export DYNAMODB_ATTEMPTS=phishing-app-dev-attempts
   export DYNAMODB_RESPONSES=phishing-app-dev-responses
   export DYNAMODB_INSPECTOR=phishing-app-dev-inspector-attempts
   export S3_BUCKET=phishing-app-dev-eu-west-3
   export SECRET_KEY=<same-secret-as-terraform>

   python seed_dynamodb.py
   ```
3. Verify the app:
   - Open the API Gateway URL in a browser.
   - Login with `admin / admin123`.
   - Confirm quiz list and Email Inspector load.

### Screenshot Checklist (Step-by-Step, Reproducible)
Use this checklist for any environment by substituting `<env>` (e.g., `dev`, `prod`).

1. [ ] **Bootstrap: S3 state bucket** (AWS console)
   - Evidence: bucket details page with versioning enabled.
   - Paste screenshot:
     - `[[PASTE: bootstrap-s3-<env>.png]]`

2. [ ] **Bootstrap: DynamoDB lock table** (AWS console)
   - Evidence: lock table details page.
   - Paste screenshot:
     - `[[PASTE: bootstrap-dynamodb-lock-<env>.png]]`

3. [ ] **Terraform init** (terminal)
   - Command: `terraform init -backend-config=backend/<env>.hcl`
   - Evidence: init success output.
   - Paste screenshot:
     - `[[PASTE: terraform-init-<env>.png]]`

4. [ ] **Terraform plan** (terminal)
   - Command: `terraform plan -var-file=env/<env>.tfvars`
   - Evidence: plan summary (add/change/destroy).
   - Paste screenshot:
     - `[[PASTE: terraform-plan-<env>.png]]`

5. [ ] **Terraform apply** (terminal)
   - Command: `terraform apply -var-file=env/<env>.tfvars`
   - Evidence: apply success + outputs (API Gateway URL).
   - Paste screenshot:
     - `[[PASTE: terraform-apply-<env>.png]]`

6. [ ] **Upload EML samples** (AWS console)
   - Evidence: `eml-samples/` prefix listing with `.eml` files.
   - Paste screenshot:
     - `[[PASTE: s3-eml-samples-<env>.png]]`

7. [ ] **Seed DynamoDB** (terminal)
   - Command: `python seed_dynamodb.py`
   - Evidence: output confirming admin + quiz created.
   - Paste screenshot:
     - `[[PASTE: seed-dynamodb-<env>.png]]`

8. [ ] **Verify login page** (browser)
   - Evidence: login page loaded from API Gateway URL.
   - Paste screenshot:
     - `[[PASTE: verify-login-<env>.png]]`

9. [ ] **Verify quiz list** (browser)
   - Evidence: successful login + quiz list page.
   - Paste screenshot:
     - `[[PASTE: verify-quiz-list-<env>.png]]`


## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| AWS CLI | v2+ | AWS resource management |
| Terraform | >= 1.5 | Infrastructure as Code |
| Python | 3.12 | Lambda runtime |
| GitLab account | — | CI/CD pipeline |
| AWS account | Free Tier eligible | Hosting |

---

## 1. AWS Account Setup

### 1.1 Create an IAM User for Terraform

```bash
# In the AWS Console → IAM → Users → Create User
# Name: terraform-deployer
# Attach policies:
#   - AmazonDynamoDBFullAccess
#   - AmazonS3FullAccess
#   - AWSLambda_FullAccess
#   - AmazonAPIGatewayAdministrator
#   - IAMFullAccess
#   - CloudWatchLogsFullAccess
```

Save the **Access Key ID** and **Secret Access Key** — you'll need them.

### 1.2 Bootstrap Terraform Remote State (S3 + DynamoDB Lock)

Terraform stores its state in S3 and uses a DynamoDB table for state locking. Bootstrap these once:

```bash
cd master-Project-Phishing/terraform/bootstrap

terraform init
terraform apply \
  -var="state_bucket_name=phishing-terraform-state" \
  -var="lock_table_name=phishing-terraform-locks" \
  -var="aws_region=eu-west-3"
```

Note: If you use multiple AWS profiles, export the correct one first:

```bash
export AWS_PROFILE=terraform-deployer
```

---

## 2. Local Deployment (Manual)

### 2.1 Configure Terraform

```bash
cd master-Project-Phishing/terraform

# Copy the example variables file
cp env/dev.tfvars.example env/dev.tfvars
cp env/prod.tfvars.example env/prod.tfvars

# Edit env/dev.tfvars or env/prod.tfvars:
#   aws_region  = "eu-west-3"
#   environment = "dev"   # or "prod"
#   app_name    = "phishing-app"
#   secret_key  = "your-random-secret-string-here"  ← generate a strong key
#
# Note: `terraform/env/*.tfvars` is gitignored to avoid leaking secrets.
#
# Alternatively, start from:
#   terraform/env/dev.tfvars.example
#   terraform/env/prod.tfvars.example
```

### 2.1.1 Configure the Remote Backend

Pick the backend config for the environment:

```bash
# For dev
terraform init -backend-config=backend/dev.hcl

# For prod
terraform init -backend-config=backend/prod.hcl
```

### 2.2 Build the Lambda Package

```bash
cd master-Project-Phishing

# Build the Lambda zip artifact
./scripts/build_lambda.sh
```

Note: The Lambda handler wraps Flask as ASGI using `asgiref` + `mangum`.

### 2.3 Deploy with Terraform

```bash
cd terraform

# Preview what will be created
terraform plan -var-file=env/dev.tfvars

# Apply (creates all AWS resources)
terraform apply -var-file=env/dev.tfvars
```

### 2.3.1 Terraform Cheat Sheet (Dev/Prod)

```bash
# Dev
terraform init -backend-config=backend/dev.hcl
terraform plan -var-file=env/dev.tfvars
terraform apply -var-file=env/dev.tfvars

# Prod
terraform init -backend-config=backend/prod.hcl
terraform plan -var-file=env/prod.tfvars
terraform apply -var-file=env/prod.tfvars
```

**Expected output after `terraform apply`:**

```
Outputs:

api_gateway_url      = "https://abc123xyz.execute-api.eu-west-3.amazonaws.com"
s3_bucket_name       = "phishing-app-prod-eu-west-3"
lambda_function_name = "phishing-app-prod-app"
dynamodb_users_table = "phishing-app-prod-users"
...
```

### 2.4 Upload EML Samples to S3

```bash
aws s3 sync examples/ s3://phishing-app-<env>-eu-west-3/eml-samples/ \
  --exclude "*" --include "*.eml"
```

### 2.5 Seed the Database

```bash
# Set environment variables to point to the real AWS tables
export AWS_REGION_NAME=eu-west-3
export DYNAMODB_USERS=phishing-app-<env>-users
export DYNAMODB_QUIZZES=phishing-app-<env>-quizzes
export DYNAMODB_ATTEMPTS=phishing-app-<env>-attempts
export DYNAMODB_RESPONSES=phishing-app-<env>-responses
export DYNAMODB_INSPECTOR=phishing-app-<env>-inspector-attempts
export S3_BUCKET=phishing-app-<env>-eu-west-3
export SECRET_KEY=your-secret-key

python seed_dynamodb.py
```

### 2.6 Verify Deployment

Visit the **API Gateway URL** from the Terraform output. You should see the login page.

---

## 3. GitLab CI/CD Deployment (Automated)

### 3.0 CI/CD Purpose
**CI** validates code changes (lint + tests + build).  
**CD** previews and applies infrastructure changes with Terraform (manual approval for deploy).

### 3.1 Configure GitLab CI/CD Variables

Go to **GitLab → Your Project → Settings → CI/CD → Variables**. Add these variables (mark sensitive ones as **Masked**):

| Variable                | Value                         | Masked? |
| ----------------------- | ----------------------------- | ------- |
| `AWS_ACCESS_KEY_ID`     | Your IAM access key           | Yes     |
| `AWS_SECRET_ACCESS_KEY` | Your IAM secret key           | Yes     |
| `AWS_DEFAULT_REGION`    | `eu-west-3`                   | No      |
| `TF_VAR_secret_key`     | Your Flask secret key         | Yes     |
| `TF_ENV`                | `dev` or `prod`               | No      |
| `TF_VAR_environment`    | `dev` or `prod`               | No      |
| `TF_VAR_app_name`       | `phishing-app`                | No      |

CI/CD generates `terraform/env/<env>.tfvars` at runtime from these variables if it does not already exist in the repo.

### 3.2 Pipeline Stages

When you push to GitLab, the pipeline runs automatically:

| Stage | What happens | Auto? |
|-------|-------------|-------|
| **lint** | Runs `flake8` on the Python code | Yes |
| **test** | Runs `pytest` with mocked AWS (moto) | Yes |
| **build** | Packages the Lambda zip artifact | Yes |
| **plan** | Runs `terraform plan` and saves the plan | Yes |
| **deploy_dev** | `terraform apply` (dev) + upload EML + seed DynamoDB | **Auto** |
| **deploy_prod** | `terraform apply` (prod) + upload EML + seed DynamoDB | **Manual click** |

### 3.3 What to Expect

1. **Push code to `main` branch** → pipeline starts
2. **lint** (30s): passes if no flake8 errors
3. **test** (1-2 min): passes if all pytest tests succeed
4. **build** (1 min): creates `lambda.zip` artifact
5. **plan** (30s): shows Terraform plan output — review it in the job logs
6. **deploy_dev** (1-2 min): auto deploys dev. Creates/updates:
   - 4 DynamoDB tables
   - 1 S3 bucket
   - 1 Lambda function
   - 1 API Gateway HTTP API
   - IAM roles and CloudWatch log groups

7. **deploy_prod** (manual): click play to deploy prod.

After each deploy, the job log shows the API Gateway URL.

### 3.3 Common CI/CD Fixes
- **Pipeline prompts for `secret_key`**: set `TF_VAR_secret_key` in GitLab variables.
- **S3 sync fails**: ensure `TF_ENV` is set so the deploy job reads outputs from the correct backend.
- **Build step permission denied**: CI runs the build script via `bash` (already configured).
- **Test artifacts missing**: `make test` generates `report.xml` for GitLab JUnit reports.

---

## 4. AWS Resources Created

After deployment, your AWS account will have:

```
DynamoDB Tables:
  phishing-app-prod-users       (+ 2 GSIs: email-index, group-index)
  phishing-app-prod-quizzes
  phishing-app-prod-attempts    (+ 2 GSIs: quiz-index, group-index)
  phishing-app-prod-responses   (+ 1 GSI: quiz-question-index)
  phishing-app-prod-inspector-attempts (+ 2 GSIs: email-index, group-index)

S3 Bucket:
  phishing-app-prod-eu-west-3/
    ├── eml-samples/             ← 6 .eml files
    ├── csv-uploads/             ← admin CSV imports (created at runtime)
    └── reports/                 ← generated reports (created at runtime)

Lambda:
  phishing-app-prod-app          (Python 3.12, 512MB, 30s timeout)

API Gateway:
  phishing-app-prod-api          (HTTP API, catch-all route → Lambda)

IAM:
  phishing-app-prod-lambda-role  (DynamoDB + S3 + CloudWatch access)

CloudWatch:
  /aws/lambda/phishing-app-prod-app
  /aws/apigateway/phishing-app-prod-api
```

### DynamoDB Usage Summary
The app uses DynamoDB as its primary datastore:

**Users table**
- Stores: username, email, password hash, admin flag, cohort fields (class/year/major)
- Used by login and CSV import

**Quizzes table**
- Stores: quiz metadata and embedded questions/answers
- Used to render quiz list and questions

**Attempts table**
- Stores: quiz scores, percentage, completion timestamp, cohort fields
- Used for admin analytics and reports

**Responses table**
- Stores: per-question responses for analytics
- Used for question-level reporting

**Inspector attempts table**
- Stores: email classification attempts, phishing signals, correctness, cohort fields
- Used for inspector analytics and reports

---

## 5. Cost Estimate

All services are within AWS Free Tier limits:

| Service | Free Tier | Expected Usage |
|---------|-----------|---------------|
| Lambda | 1M requests/month | ~100-500 requests/month |
| DynamoDB | 25 GB + 25 RCU/WCU | < 1 MB data |
| S3 | 5 GB storage | < 10 MB |
| API Gateway | 1M HTTP API calls/month | ~100-500 calls/month |
| CloudWatch | 5 GB logs | < 100 MB |
| **Total** | | **$0/month** |

---

## 6. Updating the Deployment

### Code changes only (no infra changes):

```bash
# Rebuild lambda package
pip install -r requirements.txt -t package/
cp -r app/ package/app/
cp lambda_handler.py config.py package/
cd package && zip -r ../lambda.zip . && cd ..

# Update Lambda function
aws lambda update-function-code \
  --function-name phishing-app-prod-app \
  --zip-file fileb://lambda.zip
```

---

## 6.1 Destroy & Re-Deploy (CI/CD)

### Destroy (local)
```bash
cd terraform
terraform destroy -var-file=env/<env>.tfvars
```

### Re-Deploy (CI/CD)
1. Ensure remote state still exists (S3 + DynamoDB lock).
2. Ensure GitLab variables are set (especially `TF_VAR_secret_key`).
3. Push a commit to trigger the pipeline.
4. Review the `plan` stage output.
5. Click **Play** on the `deploy` stage to apply.

Note: The app is down after destroy until deploy completes.

---

## 7. Admin Operations (Post-Deploy)

### Upload Users (CSV)
1. Log in as an admin.
2. Go to **Admin → Import Users**.
3. Upload a CSV with required columns:
   - `username`, `email`, `password`, `class`, `academic_year`, `major`
   - Optional: `group`
4. Submit and verify the import summary.

Example CSV:
```csv
username,email,password,class,academic_year,major,group
jdoe,jdoe@school.edu,TempPass123,Class A,2025,CS,engineering
asmith,asmith@school.edu,TempPass456,Class B,2025,Marketing,marketing
```

### Upload Email Samples (.eml)
Upload `.eml` files to S3 under the `eml-samples/` prefix:
```bash
aws s3 sync examples/ s3://phishing-app-<env>-eu-west-3/eml-samples/ --exclude "*" --include "*.eml"
```

### Download Reports
1. Log in as admin.
2. **Admin → Reports** for quiz/cohort reports.
3. **Admin → Inspector Analytics** for inspector cohort reports.
4. Click **Download CSV** to get a pre‑signed S3 link.

Or simply push to GitLab and let the pipeline handle it.

### Infrastructure changes:

Edit the `.tf` files, push to GitLab, review the plan, and click deploy.

---

## 7. Teardown

To destroy all AWS resources:

```bash
cd terraform
terraform destroy
```

This removes all DynamoDB tables, the Lambda function, API Gateway, S3 bucket, IAM roles, and log groups. **This is irreversible** — all data in DynamoDB and S3 will be deleted.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `terraform init` fails | Check AWS credentials: `aws sts get-caller-identity` |
| Lambda returns 502 | Check CloudWatch logs: `aws logs tail /aws/lambda/phishing-app-prod-app` |
| Login page doesn't load | Verify API Gateway URL is correct from `terraform output` |
| "No quizzes available" | Run `python seed_dynamodb.py` to seed the database |
| S3 access denied | Check IAM policy on the Lambda role |
| Import users fails | Ensure CSV has columns: `username,email,password,group` |
