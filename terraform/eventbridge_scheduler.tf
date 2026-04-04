# ─── EventBridge Scheduler Role ─────────────────────────────────────────────-

resource "aws_iam_role" "campaign_scheduler" {
  name = "${local.prefix}-campaign-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "campaign_scheduler" {
  name = "${local.prefix}-campaign-scheduler"
  role = aws_iam_role.campaign_scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.campaigns.arn
      }
    ]
  })
}

# ─── Scheduler Group ─────────────────────────────────────────────────────────

resource "aws_scheduler_schedule_group" "campaigns" {
  name = "${local.prefix}-campaigns"
}

# ─── Scheduled Campaign ─────────────────────────────────────────────────────-

resource "aws_scheduler_schedule" "campaigns" {
  count                = var.campaign_schedule_enabled ? 1 : 0
  name                 = "${local.prefix}-campaign-schedule"
  group_name           = aws_scheduler_schedule_group.campaigns.name
  schedule_expression  = var.campaign_schedule_expression
  description          = "Recurring phishing simulation campaign trigger"
  schedule_expression_timezone = "UTC"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_sqs_queue.campaigns.arn
    role_arn = aws_iam_role.campaign_scheduler.arn
    input    = jsonencode({ cohort = "All", scheduled = true })
  }
}
