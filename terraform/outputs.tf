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
