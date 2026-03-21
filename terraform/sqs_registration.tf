# ─── Registration Dead-Letter Queue ──────────────────────────────────────────

resource "aws_sqs_queue" "registration_dlq" {
  name                      = "${local.prefix}-registration-dlq"
  message_retention_seconds = 1209600 # 14 days
}

# ─── Registration Queue ───────────────────────────────────────────────────────

resource "aws_sqs_queue" "registration" {
  name                       = "${local.prefix}-registration"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 86400 # 1 day

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.registration_dlq.arn
    maxReceiveCount     = 4
  })

  sqs_managed_sse_enabled = true
}

# ─── Outputs ──────────────────────────────────────────────────────────────────

output "registration_queue_url" {
  description = "SQS registration queue URL"
  value       = aws_sqs_queue.registration.url
}

output "registration_queue_arn" {
  description = "SQS registration queue ARN"
  value       = aws_sqs_queue.registration.arn
}
