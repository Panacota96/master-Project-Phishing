# ─── AWS Secrets Manager — Application Secrets ───────────────────────────────
# Stores Flask SECRET_KEY and MSAL_CLIENT_SECRET so they are never exposed
# as plaintext Lambda environment variables (visible in the AWS console).
# The Lambda receives SECRET_ARN; config.py fetches the value at startup.

resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${local.prefix}/app-secrets"
  description             = "Flask SECRET_KEY and MSAL credentials for ${local.prefix}"
  recovery_window_in_days = 7

  tags = {
    Name = "${local.prefix}-app-secrets"
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id

  secret_string = jsonencode({
    SECRET_KEY         = var.secret_key
    MSAL_CLIENT_SECRET = var.msal_client_secret
  })
}

# ─── Outputs ──────────────────────────────────────────────────────────────────

output "app_secrets_arn" {
  description = "ARN of the Secrets Manager secret holding Flask SECRET_KEY and MSAL credentials"
  value       = aws_secretsmanager_secret.app_secrets.arn
}
