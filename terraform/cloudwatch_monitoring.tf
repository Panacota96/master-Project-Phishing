# ─── SNS Alert Topic ──────────────────────────────────────────────────────────

resource "aws_sns_topic" "alerts" {
  name = "${local.prefix}-alerts"
}

resource "aws_sns_topic_subscription" "alerts_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ─── Lambda Alarms ────────────────────────────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.prefix}-lambda-errors"
  alarm_description   = "Lambda function error count >= 5 in 5 minutes"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = aws_lambda_function.app.function_name }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 5
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration_p95" {
  alarm_name          = "${local.prefix}-lambda-duration-p95"
  alarm_description   = "Lambda P95 duration >= 25 000 ms in 5 minutes"
  namespace           = "AWS/Lambda"
  metric_name         = "Duration"
  dimensions          = { FunctionName = aws_lambda_function.app.function_name }
  extended_statistic  = "p95"
  period              = 300
  evaluation_periods  = 1
  threshold           = 25000
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${local.prefix}-lambda-throttles"
  alarm_description   = "Lambda throttles >= 1 in 5 minutes"
  namespace           = "AWS/Lambda"
  metric_name         = "Throttles"
  dimensions          = { FunctionName = aws_lambda_function.app.function_name }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}

# ─── API Gateway Alarms ───────────────────────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "apigw_5xx" {
  alarm_name          = "${local.prefix}-apigw-5xx"
  alarm_description   = "API Gateway 5xx errors >= 3 in 5 minutes"
  namespace           = "AWS/ApiGateway"
  metric_name         = "5XXError"
  dimensions          = { ApiId = aws_apigatewayv2_api.app.id }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 3
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "apigw_4xx" {
  alarm_name          = "${local.prefix}-apigw-4xx"
  alarm_description   = "API Gateway 4xx errors >= 50 in 5 minutes"
  namespace           = "AWS/ApiGateway"
  metric_name         = "4XXError"
  dimensions          = { ApiId = aws_apigatewayv2_api.app.id }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 50
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}

# ─── DynamoDB Alarm ───────────────────────────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "dynamodb_system_errors" {
  alarm_name          = "${local.prefix}-dynamodb-system-errors"
  alarm_description   = "DynamoDB system errors >= 1 in 5 minutes"
  namespace           = "AWS/DynamoDB"
  metric_name         = "SystemErrors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}

# ─── CloudWatch Dashboard ─────────────────────────────────────────────────────

resource "aws_cloudwatch_dashboard" "overview" {
  dashboard_name = "${local.prefix}-overview"

  dashboard_body = jsonencode({
    widgets = [
      # Row 1 — Lambda
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 8
        height = 6
        properties = {
          title   = "Lambda Invocations"
          metrics = [["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.app.function_name]]
          period  = 300
          stat    = "Sum"
          view    = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 0
        width  = 8
        height = 6
        properties = {
          title   = "Lambda Errors"
          metrics = [["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.app.function_name]]
          period  = 300
          stat    = "Sum"
          view    = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 0
        width  = 8
        height = 6
        properties = {
          title = "Lambda Duration (p50 / p95 / p99)"
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.app.function_name, { stat = "p50", label = "p50" }],
            ["...", { stat = "p95", label = "p95" }],
            ["...", { stat = "p99", label = "p99" }],
          ]
          period = 300
          view   = "timeSeries"
        }
      },
      # Row 2 — API Gateway
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 6
        height = 6
        properties = {
          title   = "API Gateway Request Count"
          metrics = [["AWS/ApiGateway", "Count", "ApiId", aws_apigatewayv2_api.app.id]]
          period  = 300
          stat    = "Sum"
          view    = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 6
        y      = 6
        width  = 6
        height = 6
        properties = {
          title   = "API Gateway 4xx Errors"
          metrics = [["AWS/ApiGateway", "4XXError", "ApiId", aws_apigatewayv2_api.app.id]]
          period  = 300
          stat    = "Sum"
          view    = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 6
        height = 6
        properties = {
          title   = "API Gateway 5xx Errors"
          metrics = [["AWS/ApiGateway", "5XXError", "ApiId", aws_apigatewayv2_api.app.id]]
          period  = 300
          stat    = "Sum"
          view    = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 18
        y      = 6
        width  = 6
        height = 6
        properties = {
          title   = "API Gateway Latency (p99)"
          metrics = [["AWS/ApiGateway", "Latency", "ApiId", aws_apigatewayv2_api.app.id, { stat = "p99" }]]
          period  = 300
          view    = "timeSeries"
        }
      },
      # Row 3 — DynamoDB
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title = "DynamoDB Consumed Read Capacity"
          metrics = [
            for table in [
              aws_dynamodb_table.users.name,
              aws_dynamodb_table.quizzes.name,
              aws_dynamodb_table.attempts.name,
              aws_dynamodb_table.responses.name,
              aws_dynamodb_table.inspector_attempts.name,
              aws_dynamodb_table.inspector_attempts_anon.name,
              aws_dynamodb_table.bugs.name,
              aws_dynamodb_table.answer_key_overrides.name,
              aws_dynamodb_table.cohort_tokens.name,
            ] : ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", table, { label = table }]
          ]
          period = 300
          stat   = "Sum"
          view   = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          title = "DynamoDB Consumed Write Capacity"
          metrics = [
            for table in [
              aws_dynamodb_table.users.name,
              aws_dynamodb_table.quizzes.name,
              aws_dynamodb_table.attempts.name,
              aws_dynamodb_table.responses.name,
              aws_dynamodb_table.inspector_attempts.name,
              aws_dynamodb_table.inspector_attempts_anon.name,
              aws_dynamodb_table.bugs.name,
              aws_dynamodb_table.answer_key_overrides.name,
              aws_dynamodb_table.cohort_tokens.name,
            ] : ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", table, { label = table }]
          ]
          period = 300
          stat   = "Sum"
          view   = "timeSeries"
        }
      },
    ]
  })
}

# ─── Outputs ──────────────────────────────────────────────────────────────────

output "alerts_sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarm notifications"
  value       = aws_sns_topic.alerts.arn
}
