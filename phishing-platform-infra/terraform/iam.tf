# ─── Lambda Execution Role ────────────────────────────────────────────────────

resource "aws_iam_role" "lambda" {
  name = "${local.prefix}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# DynamoDB access
resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "${local.prefix}-lambda-dynamodb"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem",
          "dynamodb:BatchGetItem",
          "dynamodb:ConditionCheckItem"
        ]
        Resource = [
          aws_dynamodb_table.users.arn,
          "${aws_dynamodb_table.users.arn}/index/*",
          aws_dynamodb_table.quizzes.arn,
          "${aws_dynamodb_table.quizzes.arn}/index/*",
          aws_dynamodb_table.attempts.arn,
          "${aws_dynamodb_table.attempts.arn}/index/*",
          aws_dynamodb_table.responses.arn,
          "${aws_dynamodb_table.responses.arn}/index/*",
          aws_dynamodb_table.inspector_attempts.arn,
          "${aws_dynamodb_table.inspector_attempts.arn}/index/*",
          aws_dynamodb_table.inspector_attempts_anon.arn,
          aws_dynamodb_table.bugs.arn,
          aws_dynamodb_table.answer_key_overrides.arn,
          aws_dynamodb_table.cohort_tokens.arn,
          "${aws_dynamodb_table.cohort_tokens.arn}/index/*",
          aws_dynamodb_table.threat_cache.arn,
          aws_dynamodb_table.campaigns.arn,
          "${aws_dynamodb_table.campaigns.arn}/index/*",
          aws_dynamodb_table.campaign_events.arn,
          "${aws_dynamodb_table.campaign_events.arn}/index/*"
        ]
      }
    ]
  })
}

# SQS access (enqueue registrations)
resource "aws_iam_role_policy" "lambda_sqs" {
  name = "${local.prefix}-lambda-sqs"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = [
          aws_sqs_queue.registration.arn,
          aws_sqs_queue.campaigns.arn
        ]
      }
    ]
  })
}

# X-Ray tracing
resource "aws_iam_role_policy" "lambda_xray" {
  name = "${local.prefix}-lambda-xray"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets",
        ]
        Resource = "*"
      }
    ]
  })
}

# S3 access
resource "aws_iam_role_policy" "lambda_s3" {
  name = "${local.prefix}-lambda-s3"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.app.arn,
          "${aws_s3_bucket.app.arn}/*"
        ]
      }
    ]
  })
}

# Secrets Manager access (read SECRET_KEY and MSAL credentials at runtime)
resource "aws_iam_role_policy" "lambda_secrets" {
  name = "${local.prefix}-lambda-secrets"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = aws_secretsmanager_secret.app_secrets.arn
      }
    ]
  })
}
