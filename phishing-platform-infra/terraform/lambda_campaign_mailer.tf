# ─── Campaign Mailer IAM Role ────────────────────────────────────────────────

resource "aws_iam_role" "campaign_mailer" {
  name = "${local.prefix}-campaign-mailer-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "campaign_mailer_logs" {
  role       = aws_iam_role.campaign_mailer.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "campaign_mailer_vpc" {
  role       = aws_iam_role.campaign_mailer.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "campaign_mailer" {
  name = "${local.prefix}-campaign-mailer"
  role = aws_iam_role.campaign_mailer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBUsers"
        Effect = "Allow"
        Action = [
          "dynamodb:Scan",
          "dynamodb:Query",
          "dynamodb:GetItem"
        ]
        Resource = [
          aws_dynamodb_table.users.arn,
          "${aws_dynamodb_table.users.arn}/index/*"
        ]
      },
      {
        Sid    = "CampaignTables"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = [
          aws_dynamodb_table.campaigns.arn,
          aws_dynamodb_table.campaign_events.arn,
          "${aws_dynamodb_table.campaign_events.arn}/index/*"
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
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.campaigns.arn
      }
    ]
  })
}

# ─── Campaign Mailer Lambda Function ─────────────────────────────────────────

resource "aws_lambda_function" "campaign_mailer" {
  function_name = "${local.prefix}-campaign-mailer"
  role          = aws_iam_role.campaign_mailer.arn
  handler       = "handler.handler"
  runtime       = "python3.12"
  memory_size   = 256
  timeout       = 120

  filename         = "${path.module}/../campaign_mailer.zip"
  source_code_hash = fileexists("${path.module}/../campaign_mailer.zip") ? filebase64sha256("${path.module}/../campaign_mailer.zip") : ""

  environment {
    variables = {
      AWS_REGION_NAME           = var.aws_region
      DYNAMODB_USERS            = aws_dynamodb_table.users.name
      DYNAMODB_CAMPAIGNS        = aws_dynamodb_table.campaigns.name
      DYNAMODB_CAMPAIGN_EVENTS  = aws_dynamodb_table.campaign_events.name
      SES_FROM_EMAIL            = var.ses_from_email
      REDIS_ENDPOINT            = "${aws_elasticache_replication_group.redis.primary_endpoint_address}:${aws_elasticache_replication_group.redis.port}"
      REDIS_USE_TLS             = "false"
      APP_LOGIN_URL             = "https://${aws_cloudfront_distribution.app.domain_name}/auth/login"
    }
  }

  vpc_config {
    subnet_ids         = data.aws_subnets.default.ids
    security_group_ids = [aws_security_group.lambda.id]
  }
}

# ─── SQS → Campaign Mailer Event Source Mapping ──────────────────────────────

resource "aws_lambda_event_source_mapping" "campaign_sqs" {
  event_source_arn = aws_sqs_queue.campaigns.arn
  function_name    = aws_lambda_function.campaign_mailer.arn
  batch_size       = 1
  enabled          = true
}

# ─── CloudWatch Log Group ─────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "campaign_mailer" {
  name              = "/aws/lambda/${aws_lambda_function.campaign_mailer.function_name}"
  retention_in_days = 14
}
