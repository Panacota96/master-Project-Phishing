# ─── SES Email Identity ───────────────────────────────────────────────────────
# Verifies the sender address used for registration confirmation emails.
# Set var.ses_from_email to a verified address (e.g. no-reply@engarde.esme.fr).

resource "aws_ses_email_identity" "from" {
  count = var.ses_from_email != "" ? 1 : 0
  email = var.ses_from_email
}

# ─── SNS Registration Topic ───────────────────────────────────────────────────
# Pub/sub for registration events — the worker Lambda is triggered directly
# by SQS; this topic is available for future fan-out (e.g. admin notifications).

resource "aws_sns_topic" "registration" {
  name = "${local.prefix}-registration"
}

output "registration_sns_topic_arn" {
  description = "SNS topic ARN for registration events"
  value       = aws_sns_topic.registration.arn
}
