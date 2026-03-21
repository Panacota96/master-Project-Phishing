# Deployment Procedures — Phishing Awareness Training

![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=github-actions&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?logo=terraform&logoColor=white)
![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?logo=awslambda&logoColor=white)
![Amazon S3](https://img.shields.io/badge/Amazon_S3-569A31?logo=amazons3&logoColor=white)
![DynamoDB](https://img.shields.io/badge/DynamoDB-4053D6?logo=amazondynamodb&logoColor=white)

## Prerequisites

- **AWS CLI**: Configured with the appropriate IAM permissions.
- **Terraform**: Version 1.5+ for infrastructure management.
- **Python 3.12+**: For local packaging and seeding.

---

## First-Time Setup: Bootstrap Terraform State

Before deploying for the first time, create the Terraform state bucket and lock table:

```bash
cd terraform/bootstrap
terraform init
terraform apply \
  -var="state_bucket_name=phishing-terraform-state" \
  -var="lock_table_name=phishing-terraform-locks" \
  -var="aws_region=eu-west-3"
```

---

## GitHub Environment Setup

Deployments run via GitHub Actions using **OIDC** (no static AWS credentials stored).

### 1. Create GitHub Environments

In your GitHub repository, go to **Settings → Environments** and create two environments:

| Environment | Approval requirement |
|---|---|
| `dev` | None — auto-deploys on push to `main` |
| `prod` | Add required reviewers — prevents accidental production deploys |

### 2. Add Required Secrets

In each environment (or at the repository level), add:

| Secret name | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | Output from `terraform output github_actions_deploy_role_arn` after bootstrap |
| `TF_VAR_SECRET_KEY` | Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"` |

> No `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` needed — OIDC handles authentication.

---

## Step 1: Lambda Packaging

The application must be packaged with its dependencies for deployment to AWS Lambda.

```bash
# Build Flask app artifact
./scripts/build_lambda.sh    # or: make lambda

# Build registration worker artifact
make registration-worker
```

This generates:
- `lambda.zip` — Flask app + dependencies
- `registration_worker.zip` — SQS worker Lambda

---

## Step 2: Terraform Infrastructure

Infrastructure changes are managed via Terraform:

```bash
cd terraform/

# Initialize (first time or environment change)
terraform init -reconfigure -backend-config="backend/dev.hcl"

# Plan changes
terraform plan -var-file="env/dev.tfvars" -out=tfplan

# Apply changes
terraform apply tfplan
```

For production, substitute `dev` with `prod` in the backend config and tfvars paths.

---

## Step 3: Sync Assets to S3

After `terraform apply`, sync EML samples and training videos:

```bash
# Sync EML email samples
aws s3 sync examples/ s3://phishing-app-<env>-eu-west-3/eml-samples/ \
  --exclude "*" --include "*.eml"

# Sync training videos
aws s3 sync app/static/videos/ s3://phishing-app-<env>-eu-west-3/videos/ \
  --exclude "*" --include "*.mp4" --region eu-west-3
```

Or use the combined make target (reads bucket name from Terraform output):

```bash
make sync-assets
```

---

## Step 4: Seed DynamoDB

If this is a new environment, seed the admin user and quizzes:

```bash
python3 seed_dynamodb.py
```

To skip seeding on subsequent deploys, set the `skip_seed` input to `true` in the `workflow_dispatch` form.

---

## Step 5: Verification

1. **Health check**: Visit the CloudFront URL (from `terraform output cloudfront_url`) and verify the login page loads.
2. **Login**: Use the admin credentials (`admin` / `admin123`) — change immediately in production.
3. **Inspector access**: Verify that `.eml` files can be retrieved from S3 and loaded into the inspector.
4. **CloudWatch**: Check `/aws/lambda/phishing-app-<env>-app` log group for any Lambda errors.

---

## Automated Deployment (GitHub Actions)

Once GitHub Environments and secrets are configured, deployments run automatically:

- **Push to `main`** → triggers `ci.yml` (lint/test/build) → `deploy-dev.yml` (plan → apply → sync → seed)
- **Production** → manually trigger `deploy-prod.yml` from the Actions tab; requires prod environment approval

See [`CICD.md`](CICD.md) for the full pipeline diagram and workflow details.

---

## Special Considerations

- **Lambda Memory & Timeout**: For large `.eml` files or high traffic, increase `lambda_memory_size` (default: 512 MB) and `lambda_timeout` (default: 30 s) in `terraform/variables.tf`.
- **API Gateway Throttling**: Configure rate limiting in `terraform/api_gateway.tf` if needed.
- **Videos not loading**: Set `VIDEO_BASE_URL` to the S3 base URL and re-run `seed_dynamodb.py`.
  Example: `VIDEO_BASE_URL=https://phishing-app-dev-eu-west-3.s3.eu-west-3.amazonaws.com/videos`

---

## Post-Deployment

- **Monitor Logs**: CloudWatch Logs at `/aws/lambda/phishing-app-<env>-app`
- **Database Status**: Check DynamoDB tables for correct seeding
- **SSL/TLS**: CloudFront provides HTTPS by default; custom domain + ACM is optional
- **Teardown**: Use `destroy.yml` workflow dispatch to tear down an environment
