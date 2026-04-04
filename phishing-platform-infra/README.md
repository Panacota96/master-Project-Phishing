# phishing-platform-infra — Infrastructure & Operations

Infrastructure assets for the EnGarde phishing awareness app. Use this folder as a standalone `phishing-platform-infra` repository (Terraform state, Ansible playbooks, legacy EC2 helpers, and infra/migration scripts).

## Layout

- `terraform/` — AWS IaC (Lambda, API Gateway, DynamoDB, S3, CloudFront, IAM, SQS/SNS, CloudWatch)
- `terraform/bootstrap/` — Remote state bootstrap (S3 bucket + DynamoDB lock table)
- `terraform/backend/` — Backend configs for dev/prod state
- `terraform/env/` — Example tfvars for dev/prod
- `ansible/` — Optional VM deployment playbooks
- `aws/` — Legacy EC2 user-data scripts and AMI notes
- `scripts/` — Infra + migration helpers:
  - `import_resources.sh`
  - `migrate_dynamodb.py`
  - `migrate_inspector_attempts.py`
  - `migrate_s3.sh`
- `terraform.tfstate` — Local state snapshot (use remote state for real deployments)

## Terraform Quickstart

```bash
cd terraform
# Bootstrap remote state (one-time)
terraform -chdir=bootstrap init
terraform -chdir=bootstrap apply \
  -var="state_bucket_name=phishing-terraform-state" \
  -var="lock_table_name=phishing-terraform-locks" \
  -var="aws_region=eu-west-3"

# Configure backend + variables
terraform init -backend-config=backend/dev.hcl
cp env/dev.tfvars.example env/dev.tfvars   # edit secrets before running

# Plan and apply
terraform plan -var-file=env/dev.tfvars -out=tfplan
terraform apply tfplan
```

Key outputs used by the app (pass as env vars in `phishing-platform-app`):
- `s3_bucket_name` → `S3_BUCKET`
- `cloudfront_url` → student-facing URL (or `app_url` from API Gateway)
- DynamoDB table outputs → `DYNAMODB_*` variables
- `github_actions_deploy_role_arn` → `AWS_DEPLOY_ROLE_ARN` for CI

## Migration Helpers

```bash
# Import existing AWS resources into state
./scripts/import_resources.sh

# Sync S3 buckets and DynamoDB tables between environments
./scripts/migrate_s3.sh
python3 ./scripts/migrate_dynamodb.py --from dev --to prod

# Migrate legacy inspector attempts to anonymous table
python3 ./scripts/migrate_inspector_attempts.py --dry-run
python3 ./scripts/migrate_inspector_attempts.py
```

## CI/CD Note

Deploy, destroy, and plan workflows in the app repo reference `phishing-platform-infra/terraform` as their working directory. When splitting repositories, move those workflows into this folder’s `.github/workflows/` and keep `ci.yml` in the app repo.
