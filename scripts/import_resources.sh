#!/usr/bin/env bash
set -euo pipefail

TF_ENV="${TF_ENV:-dev}"
APP_NAME="${TF_VAR_app_name:-phishing-app}"
REGION="${AWS_DEFAULT_REGION:-eu-west-3}"

cd "$(dirname "$0")/../terraform"

terraform init -reconfigure -backend-config="backend/${TF_ENV}.hcl" >/dev/null

state_has() {
  terraform state list | grep -q "^$1$" >/dev/null 2>&1
}

import_if_missing() {
  local addr="$1"
  local id="$2"
  if state_has "$addr"; then
    echo "- Skipping $addr (already in state)"
  else
    echo "+ Importing $addr"
    terraform import "$addr" "$id"
  fi
}

BUCKET_NAME="${APP_NAME}-${TF_ENV}-${REGION}"
LAMBDA_NAME="${APP_NAME}-${TF_ENV}-app"
API_NAME="${APP_NAME}-${TF_ENV}-api"
ROLE_NAME="${APP_NAME}-${TF_ENV}-lambda-role"

# S3 bucket + configs
import_if_missing aws_s3_bucket.app "$BUCKET_NAME"
import_if_missing aws_s3_bucket_public_access_block.app "$BUCKET_NAME"
import_if_missing aws_s3_bucket_server_side_encryption_configuration.app "$BUCKET_NAME"
import_if_missing aws_s3_bucket_versioning.app "$BUCKET_NAME"

# DynamoDB tables
import_if_missing aws_dynamodb_table.users "${APP_NAME}-${TF_ENV}-users"
import_if_missing aws_dynamodb_table.quizzes "${APP_NAME}-${TF_ENV}-quizzes"
import_if_missing aws_dynamodb_table.attempts "${APP_NAME}-${TF_ENV}-attempts"
import_if_missing aws_dynamodb_table.responses "${APP_NAME}-${TF_ENV}-responses"
import_if_missing aws_dynamodb_table.inspector_attempts "${APP_NAME}-${TF_ENV}-inspector-attempts"

# IAM role + policies
import_if_missing aws_iam_role.lambda "$ROLE_NAME"
import_if_missing aws_iam_role_policy.lambda_dynamodb "$ROLE_NAME:${APP_NAME}-${TF_ENV}-lambda-dynamodb"
import_if_missing aws_iam_role_policy.lambda_s3 "$ROLE_NAME:${APP_NAME}-${TF_ENV}-lambda-s3"
import_if_missing aws_iam_role_policy_attachment.lambda_logs "$ROLE_NAME/arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

# CloudWatch log groups
import_if_missing aws_cloudwatch_log_group.apigw "/aws/apigateway/${API_NAME}"
import_if_missing aws_cloudwatch_log_group.lambda "/aws/lambda/${LAMBDA_NAME}"

# Lambda function
import_if_missing aws_lambda_function.app "$LAMBDA_NAME"

# API Gateway integration/route/stage/permission
API_ID="$(aws apigatewayv2 get-apis --query "Items[?Name=='${API_NAME}'].ApiId | [0]" --output text)"
if [ -z "$API_ID" ] || [ "$API_ID" = "None" ]; then
  echo "ERROR: Could not find API Gateway ID for ${API_NAME}." >&2
  exit 1
fi
if ! state_has aws_apigatewayv2_api.app; then
  terraform import aws_apigatewayv2_api.app "$API_ID"
fi

INTEGRATION_ID="$(aws apigatewayv2 get-integrations --api-id "$API_ID" --query 'Items[0].IntegrationId' --output text)"
ROUTE_ID="$(aws apigatewayv2 get-routes --api-id "$API_ID" --query 'Items[0].RouteId' --output text)"

if [ -z "$INTEGRATION_ID" ] || [ "$INTEGRATION_ID" = "None" ]; then
  echo "ERROR: Could not find integration for API ${API_ID}." >&2
  exit 1
fi
if [ -z "$ROUTE_ID" ] || [ "$ROUTE_ID" = "None" ]; then
  echo "ERROR: Could not find route for API ${API_ID}." >&2
  exit 1
fi

import_if_missing aws_apigatewayv2_integration.lambda "$INTEGRATION_ID"
import_if_missing aws_apigatewayv2_route.default "$ROUTE_ID"
import_if_missing aws_apigatewayv2_stage.default "${API_ID}/\$default"
import_if_missing aws_lambda_permission.apigw "${LAMBDA_NAME}/AllowAPIGatewayInvoke"

echo "All imports complete. Run: terraform plan -var-file=env/${TF_ENV}.tfvars"
