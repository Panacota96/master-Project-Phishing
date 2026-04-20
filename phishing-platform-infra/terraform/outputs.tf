output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_api.app.api_endpoint
}

output "s3_bucket_name" {
  description = "S3 bucket name for the application"
  value       = aws_s3_bucket.app.id
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.app.arn
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.app.function_name
}

output "dynamodb_users_table" {
  description = "DynamoDB users table name"
  value       = aws_dynamodb_table.users.name
}

output "dynamodb_quizzes_table" {
  description = "DynamoDB quizzes table name"
  value       = aws_dynamodb_table.quizzes.name
}

output "dynamodb_attempts_table" {
  description = "DynamoDB attempts table name"
  value       = aws_dynamodb_table.attempts.name
}

output "dynamodb_responses_table" {
  description = "DynamoDB responses table name"
  value       = aws_dynamodb_table.responses.name
}

output "dynamodb_inspector_table" {
  description = "DynamoDB inspector attempts table name"
  value       = aws_dynamodb_table.inspector_attempts.name
}

output "dynamodb_inspector_anon_table" {
  description = "DynamoDB anonymous inspector attempts table name"
  value       = aws_dynamodb_table.inspector_attempts_anon.name
}

output "dynamodb_answer_key_overrides_table" {
  description = "DynamoDB answer key overrides table name"
  value       = aws_dynamodb_table.answer_key_overrides.name
}

output "dynamodb_bugs_table" {
  description = "DynamoDB bug reports table name"
  value       = aws_dynamodb_table.bugs.name
}

output "dynamodb_threat_cache_table" {
  description = "DynamoDB threat cache table name"
  value       = aws_dynamodb_table.threat_cache.name
}

output "dynamodb_campaigns_table" {
  description = "DynamoDB campaigns table name"
  value       = aws_dynamodb_table.campaigns.name
}

output "dynamodb_campaign_events_table" {
  description = "DynamoDB campaign events table name"
  value       = aws_dynamodb_table.campaign_events.name
}

output "cloudfront_url" {
  description = "Stable CloudFront URL for the application (share this with students)"
  value       = "https://${aws_cloudfront_distribution.app.domain_name}"
}

output "app_url" {
  description = "Application URL (custom domain if configured, otherwise CloudFront)"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_cloudfront_distribution.app.domain_name}"
}

output "custom_domain_url" {
  description = "Custom domain URL (empty if not configured)"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : ""
}

