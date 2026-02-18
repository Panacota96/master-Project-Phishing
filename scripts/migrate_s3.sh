#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${TF_VAR_app_name:-phishing-app}"
REGION="${AWS_DEFAULT_REGION:-eu-west-3}"
DEV_ENV="${DEV_ENV:-dev}"
PROD_ENV="${PROD_ENV:-prod}"

DEV_BUCKET="${DEV_BUCKET:-${APP_NAME}-${DEV_ENV}-${REGION}}"
PROD_BUCKET="${PROD_BUCKET:-${APP_NAME}-${PROD_ENV}-${REGION}}"

PREFIXES=("eml-samples" "reports" "csv-uploads")

echo "Migrating S3 prefixes from ${DEV_BUCKET} -> ${PROD_BUCKET}"
for prefix in "${PREFIXES[@]}"; do
  echo "Syncing s3://${DEV_BUCKET}/${prefix}/ -> s3://${PROD_BUCKET}/${prefix}/"
  aws s3 sync "s3://${DEV_BUCKET}/${prefix}/" "s3://${PROD_BUCKET}/${prefix}/"
done

echo "S3 migration complete."
