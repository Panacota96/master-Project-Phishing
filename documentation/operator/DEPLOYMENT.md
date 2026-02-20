# Deployment Procedures - Phishing Awareness Training

## Prerequisites
- **AWS CLI**: Configured with the appropriate IAM permissions.
- **Terraform**: Version 1.5+ for infrastructure management.
- **Python 3.12+**: For local packaging and seeding.

## Step 1: Lambda Packaging
The application must be packaged with its dependencies for deployment to AWS Lambda.
```bash
# Locally
./scripts/build_lambda.sh
```
This generates `lambda.zip` containing the Flask app (`app/`), `lambda_handler.py`, and all required packages (`package/`).

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

## Step 3: Deployment Checklist
1. **Verify Lambda Build**: Ensure `lambda.zip` is up-to-date.
2. **Review Infrastructure Changes**: Always check the `terraform plan` output.
3. **Database Seeding**: If the environment is new, run `seed_dynamodb.py` to initialize tables.
4. **Environment Variables**: Verify `SECRET_KEY` and `AWS_REGION_NAME` are correctly set.
5. **API Gateway URL**: Once deployed, the API Gateway URL will be available in the Terraform outputs.

## Step 4: Verification
- **Health Check**: Visit the API Gateway URL and verify the login page loads.
- **Login**: Use the admin credentials (`admin` / `admin123`) to log in.
- **Inspector Access**: Verify that example `.eml` files can be retrieved from S3 and loaded into the inspector.

## Special Considerations
- **Lambda Memory & Timeout**: For large `.eml` files or high traffic, increase `lambda_memory_size` (default: 512MB) and `lambda_timeout` (default: 30s) in `terraform/variables.tf`.
- **API Gateway Throttling**: Configure rate limiting in `terraform/api_gateway.tf` if needed.
- **S3 Sync**: Ensure `.eml` files are synced to the application bucket's `eml-samples/` prefix:
    ```bash
    aws s3 sync examples/ s3://phishing-app-<env>-eu-west-3/eml-samples/ --exclude "*" --include "*.eml"
    ```

## Post-Deployment
- **Monitor Logs**: Use CloudWatch Logs (`/aws/lambda/<function-name>`) for troubleshooting.
- **Database Status**: Check DynamoDB tables for correct seeding and table status.
- **SSL/TLS**: API Gateway provides an HTTPS endpoint by default.
- **Domain Names**: If using a custom domain, configure Route 53 and ACM (optional).
