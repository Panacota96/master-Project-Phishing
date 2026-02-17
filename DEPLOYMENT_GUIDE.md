# Deployment Guide — Serverless AWS (Terraform + GitLab CI/CD)

This guide explains how to deploy the phishing awareness app to AWS using Terraform and GitLab CI/CD.

---

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

### 1.2 Create the Terraform State Bucket

Terraform stores its state in S3. Create this bucket once:

```bash
aws s3 mb s3://phishing-terraform-state --region eu-west-3
aws s3api put-bucket-versioning \
  --bucket phishing-terraform-state \
  --versioning-configuration Status=Enabled
```

---

## 2. Local Deployment (Manual)

### 2.1 Configure Terraform

```bash
cd master-Project-Phishing/terraform

# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars:
#   aws_region  = "eu-west-3"
#   environment = "prod"
#   app_name    = "phishing-app"
#   secret_key  = "your-random-secret-string-here"  ← generate a strong key
```

### 2.2 Build the Lambda Package

```bash
cd master-Project-Phishing

# Install dependencies into a package/ directory
pip install -r requirements.txt -t package/

# Copy application code
cp -r app/ package/app/
cp lambda_handler.py config.py package/

# Create the zip
cd package && zip -r ../lambda.zip . && cd ..
```

### 2.3 Deploy with Terraform

```bash
cd terraform

# Initialize Terraform (downloads providers, sets up backend)
terraform init

# Preview what will be created
terraform plan

# Apply (creates all AWS resources)
terraform apply
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
aws s3 sync examples/ s3://phishing-app-prod-eu-west-3/eml-samples/ \
  --exclude "*" --include "*.eml"
```

### 2.5 Seed the Database

```bash
# Set environment variables to point to the real AWS tables
export AWS_REGION_NAME=eu-west-3
export DYNAMODB_USERS=phishing-app-prod-users
export DYNAMODB_QUIZZES=phishing-app-prod-quizzes
export DYNAMODB_ATTEMPTS=phishing-app-prod-attempts
export DYNAMODB_RESPONSES=phishing-app-prod-responses
export S3_BUCKET=phishing-app-prod-eu-west-3
export SECRET_KEY=your-secret-key

python seed_dynamodb.py
```

### 2.6 Verify Deployment

Visit the **API Gateway URL** from the Terraform output. You should see the login page.

---

## 3. GitLab CI/CD Deployment (Automated)

### 3.1 Configure GitLab CI/CD Variables

Go to **GitLab → Your Project → Settings → CI/CD → Variables**. Add these variables (mark sensitive ones as **Masked**):

| Variable | Value | Masked? |
|----------|-------|---------|
| `AWS_ACCESS_KEY_ID` | Your IAM access key | Yes |
| `AWS_SECRET_ACCESS_KEY` | Your IAM secret key | Yes |
| `AWS_DEFAULT_REGION` | `eu-west-3` | No |
| `TF_VAR_secret_key` | Your Flask secret key | Yes |
| `TF_VAR_environment` | `prod` | No |
| `TF_VAR_app_name` | `phishing-app` | No |
| `S3_BUCKET` | `phishing-app-prod-eu-west-3` | No |

### 3.2 Pipeline Stages

When you push to GitLab, the pipeline runs automatically:

| Stage | What happens | Auto? |
|-------|-------------|-------|
| **lint** | Runs `flake8` on the Python code | Yes |
| **test** | Runs `pytest` with mocked AWS (moto) | Yes |
| **build** | Packages the Lambda zip artifact | Yes |
| **plan** | Runs `terraform plan` and saves the plan | Yes |
| **deploy** | Runs `terraform apply` + uploads EML files to S3 | **Manual click** |

### 3.3 What to Expect

1. **Push code to `main` branch** → pipeline starts
2. **lint** (30s): passes if no flake8 errors
3. **test** (1-2 min): passes if all pytest tests succeed
4. **build** (1 min): creates `lambda.zip` artifact
5. **plan** (30s): shows Terraform plan output — review it in the job logs
6. **deploy** (1-2 min): click the play button to deploy. Creates/updates:
   - 4 DynamoDB tables
   - 1 S3 bucket
   - 1 Lambda function
   - 1 API Gateway HTTP API
   - IAM roles and CloudWatch log groups

After deploy, the job log shows the API Gateway URL.

---

## 4. AWS Resources Created

After deployment, your AWS account will have:

```
DynamoDB Tables:
  phishing-app-prod-users       (+ 2 GSIs: email-index, group-index)
  phishing-app-prod-quizzes
  phishing-app-prod-attempts    (+ 2 GSIs: quiz-index, group-index)
  phishing-app-prod-responses   (+ 1 GSI: quiz-question-index)

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
