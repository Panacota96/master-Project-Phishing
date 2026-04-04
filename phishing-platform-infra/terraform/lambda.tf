# ─── Lambda Function ──────────────────────────────────────────────────────────

resource "aws_lambda_function" "app" {
  function_name = "${local.prefix}-app"
  role          = aws_iam_role.lambda.arn
  handler       = "lambda_handler.handler"
  runtime       = "python3.12"
  memory_size   = var.lambda_memory_size
  timeout       = var.lambda_timeout

  filename         = "${path.module}/../lambda.zip"
  source_code_hash = fileexists("${path.module}/../lambda.zip") ? filebase64sha256("${path.module}/../lambda.zip") : ""

  environment {
    variables = {
      FLASK_ENV          = var.environment
      SECRET_ARN         = aws_secretsmanager_secret.app_secrets.arn
      AWS_REGION_NAME    = var.aws_region
      DYNAMODB_USERS     = aws_dynamodb_table.users.name
      DYNAMODB_QUIZZES   = aws_dynamodb_table.quizzes.name
      DYNAMODB_ATTEMPTS  = aws_dynamodb_table.attempts.name
      DYNAMODB_RESPONSES = aws_dynamodb_table.responses.name
      DYNAMODB_INSPECTOR = aws_dynamodb_table.inspector_attempts.name
      DYNAMODB_INSPECTOR_ANON       = aws_dynamodb_table.inspector_attempts_anon.name
      DYNAMODB_BUGS                 = aws_dynamodb_table.bugs.name
      DYNAMODB_ANSWER_KEY_OVERRIDES = aws_dynamodb_table.answer_key_overrides.name
      DYNAMODB_COHORT_TOKENS        = aws_dynamodb_table.cohort_tokens.name
      DYNAMODB_THREAT_CACHE         = aws_dynamodb_table.threat_cache.name
      DYNAMODB_CAMPAIGNS            = aws_dynamodb_table.campaigns.name
      DYNAMODB_CAMPAIGN_EVENTS      = aws_dynamodb_table.campaign_events.name
      S3_BUCKET                     = aws_s3_bucket.app.id
      SQS_REGISTRATION_QUEUE_URL    = aws_sqs_queue.registration.url
      SQS_CAMPAIGN_QUEUE_URL        = aws_sqs_queue.campaigns.url
      SES_FROM_EMAIL                = var.ses_from_email
      APP_LOGIN_URL                 = "https://${aws_cloudfront_distribution.app.domain_name}/auth/login"
      REDIS_ENDPOINT                = "${aws_elasticache_replication_group.redis.primary_endpoint_address}:${aws_elasticache_replication_group.redis.port}"
      REDIS_USE_TLS                 = "false"
      CAMPAIGN_LAMBDA_ARN           = aws_lambda_function.campaign_mailer.arn
      MSAL_CLIENT_ID                = var.msal_client_id
      MSAL_CLIENT_SECRET            = var.msal_client_secret
      MSAL_AUTHORITY                = var.msal_authority
      MSAL_ADMIN_GROUP_ID           = var.msal_admin_group_id
      MSAL_INSTRUCTOR_GROUP_ID      = var.msal_instructor_group_id
    }
  }

  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }

  vpc_config {
    subnet_ids         = data.aws_subnets.default.ids
    security_group_ids = [aws_security_group.lambda.id]
  }
}

# ─── CloudWatch Log Group ─────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.app.function_name}"
  retention_in_days = 14
}

# ─── Lambda Permission for API Gateway ────────────────────────────────────────

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.app.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.app.execution_arn}/*/*"
}
