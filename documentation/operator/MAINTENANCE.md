# Maintenance and Operations - Phishing Awareness Training

## Database Migrations
Database schema changes are infrequent in DynamoDB, but data migrations may be necessary:
- **`scripts/migrate_dynamodb.py`**: Migrates users and quiz definitions between environments (`dev` to `prod`).
    - **Usage**: `python3 scripts/migrate_dynamodb.py --from dev --to prod`
- **`scripts/migrate_s3.sh`**: Syncs EML samples and Lambda artifacts across environments.
    - **Usage**: `bash scripts/migrate_s3.sh`
- **`scripts/migrate_inspector_attempts.py`**: GDPR-safe migration of old inspector attempts to the anonymous table.
    - **Usage**: `python3 scripts/migrate_inspector_attempts.py`

## User Management
For large cohorts, bulk importing users from CSV is the most efficient method:
1. **Prepare CSV**: Required columns: `username`, `email`, `password`, `class_name`, `academic_year`, `major`, `facility` (all mandatory), `group` (optional, defaults to `default`).
   ```
   username,email,password,class_name,academic_year,major,facility,group
   jdoe,jdoe@example.com,pass123,Class A,2025,CS,Paris,lab-1
   ```
2. **Import via UI**: Login as admin and use **Admin → Import Users**.
3. **Seeding Script**: For initial environment setup, use `seed_dynamodb.py`.

## Answer Key Management
The Inspector's ground-truth answer key can be edited without a code deployment:
- Go to **Admin → Inspector Analytics → View Answer Key & Troubleshoot**
- Click **Edit** on any email row to change its classification (Phishing/Spam) or required signals
- Overrides are stored in the `DYNAMODB_ANSWER_KEY_OVERRIDES` table and take effect immediately
- Click **Reset to Default** to revert to the static `app/inspector/answer_key.py` baseline

## Monitoring & Troubleshooting
- **CloudWatch Logs**: Check logs at `/aws/lambda/phishing-app-<env>-app` for runtime errors.
- **DynamoDB Capacity**: Monitor Read and Write capacity units (RCU/WCU) in the AWS Console. All tables use "Pay-Per-Request" billing to automatically scale.
- **S3 Bucket Integrity**: Ensure `eml-samples/` and `videos/` (if using S3 for videos) prefixes have the correct objects and permissions.

## Backup and Recovery
- **DynamoDB Backups**: Enable "Point-In-Time Recovery" (PITR) for critical tables (`-users`, `-attempts`, `-inspector-attempts`) in the AWS Console or Terraform.
- **S3 Versioning**: Versioning is enabled on the primary S3 bucket for data recovery.
- **Infrastructure Code**: The `terraform/` directory is the authoritative source for the environment. Ensure all changes are committed to Git.

## Common Issues & Fixes
- **`lambda.zip` Not Updating**: Re-run `./scripts/build_lambda.sh` and ensure the `source_code_hash` in `terraform/lambda.tf` triggers a redeploy.
- **Videos Not Loading**: Verify `VIDEO_BASE_URL` in the environment and ensure the S3 objects have public read access.
- **Inspector Email Not Found**: Ensure the `.eml` file exists in the S3 bucket's `eml-samples/` prefix and matches the filename in the database.
- **IAM Permission Denied**: Check the Lambda execution role for `dynamodb:*` and `s3:GetObject` permissions for the correct resources.

## Regular Maintenance Tasks
- **Monthly**: Review CloudWatch Logs for recurring errors or high latency.
- **Quarterly**: Audit user access and roles.
- **Annually**: Rotate `SECRET_KEY` and review AWS IAM permissions.
- **On Demand**: Reset quiz or inspector attempts for students via the **Admin Dashboard**.
