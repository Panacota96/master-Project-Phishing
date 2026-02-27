# ─── Lambda Function ──────────────────────────────────────────────────────────

resource "aws_lambda_function" "app" {
  function_name = "${local.prefix}-app"
  role          = aws_iam_role.lambda.arn
  handler       = "lambda_handler.handler"
  runtime       = "python3.12"
  memory_size   = var.lambda_memory_size
  timeout       = var.lambda_timeout

  filename         = "${path.module}/../lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambda.zip")

  environment {
    variables = {
      FLASK_ENV          = var.environment
      SECRET_KEY         = var.secret_key
      AWS_REGION_NAME    = var.aws_region
      DYNAMODB_USERS     = aws_dynamodb_table.users.name
      DYNAMODB_QUIZZES   = aws_dynamodb_table.quizzes.name
      DYNAMODB_ATTEMPTS  = aws_dynamodb_table.attempts.name
      DYNAMODB_RESPONSES = aws_dynamodb_table.responses.name
      DYNAMODB_INSPECTOR = aws_dynamodb_table.inspector_attempts.name
      DYNAMODB_INSPECTOR_ANON = aws_dynamodb_table.inspector_attempts_anon.name
      DYNAMODB_BUGS                = aws_dynamodb_table.bugs.name
      DYNAMODB_ANSWER_KEY_OVERRIDES = aws_dynamodb_table.answer_key_overrides.name
      S3_BUCKET                    = aws_s3_bucket.app.id
    }
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
