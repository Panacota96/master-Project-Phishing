# Terraform Remote State Bootstrap

Creates the S3 bucket and DynamoDB lock table used for Terraform remote state.

## Usage

```bash
cd terraform/bootstrap
terraform init
terraform apply \
  -var="state_bucket_name=phishing-terraform-state" \
  -var="lock_table_name=phishing-terraform-locks" \
  -var="aws_region=eu-west-3"
```

## Outputs

- `state_bucket_name`
- `lock_table_name`
