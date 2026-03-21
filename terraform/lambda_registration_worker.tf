# ─── Registration Worker IAM Role ─────────────────────────────────────────────

resource "aws_iam_role" "registration_worker" {
  name = "${local.prefix}-registration-worker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "registration_worker_logs" {
  role       = aws_iam_role.registration_worker.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "registration_worker" {
  name = "${local.prefix}-registration-worker"
  role = aws_iam_role.registration_worker.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBUsers"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
        ]
        Resource = [
          aws_dynamodb_table.users.arn,
          "${aws_dynamodb_table.users.arn}/index/*",
        ]
      },
      {
        Sid      = "SES"
        Effect   = "Allow"
        Action   = ["ses:SendEmail"]
        Resource = "*"
      },
      {
        Sid    = "SQS"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = aws_sqs_queue.registration.arn
      },
      {
        Sid      = "SNS"
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = aws_sns_topic.registration.arn
      },
    ]
  })
}

# ─── Registration Worker Lambda Function ──────────────────────────────────────

resource "aws_lambda_function" "registration_worker" {
  function_name = "${local.prefix}-registration-worker"
  role          = aws_iam_role.registration_worker.arn
  handler       = "handler.handler"
  runtime       = "python3.12"
  memory_size   = 256
  timeout       = 60

  filename         = "${path.module}/../registration_worker.zip"
  source_code_hash = fileexists("${path.module}/../registration_worker.zip") ? filebase64sha256("${path.module}/../registration_worker.zip") : ""

  environment {
    variables = {
      DYNAMODB_USERS        = aws_dynamodb_table.users.name
      AWS_REGION_NAME       = var.aws_region
      SES_FROM_EMAIL        = var.ses_from_email
      APP_LOGIN_URL         = "https://${aws_cloudfront_distribution.app.domain_name}/auth/login"
      SNS_REGISTRATION_ARN  = aws_sns_topic.registration.arn
    }
  }
}

# ─── SQS → Worker Event Source Mapping ────────────────────────────────────────

resource "aws_lambda_event_source_mapping" "registration_sqs" {
  event_source_arn = aws_sqs_queue.registration.arn
  function_name    = aws_lambda_function.registration_worker.arn
  batch_size       = 1
  enabled          = true
}

# ─── CloudWatch Log Group ─────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "registration_worker" {
  name              = "/aws/lambda/${aws_lambda_function.registration_worker.function_name}"
  retention_in_days = 14
}
