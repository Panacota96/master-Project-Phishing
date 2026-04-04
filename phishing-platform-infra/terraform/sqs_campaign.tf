# ─── Campaign Dead-Letter Queue ─────────────────────────────────────────────-

resource "aws_sqs_queue" "campaign_dlq" {
  name                      = "${local.prefix}-campaign-dlq"
  message_retention_seconds = 1209600 # 14 days
}

# ─── Campaign Queue ───────────────────────────────────────────────────────────

resource "aws_sqs_queue" "campaigns" {
  name                       = "${local.prefix}-campaigns"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 604800 # 7 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.campaign_dlq.arn
    maxReceiveCount     = 4
  })

  sqs_managed_sse_enabled = true
}

# ─── Outputs ──────────────────────────────────────────────────────────────────

output "campaign_queue_url" {
  description = "SQS campaign queue URL"
  value       = aws_sqs_queue.campaigns.url
}

output "campaign_queue_arn" {
  description = "SQS campaign queue ARN"
  value       = aws_sqs_queue.campaigns.arn
}
