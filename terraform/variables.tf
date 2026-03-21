variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-west-3"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "app_name" {
  description = "Application name used as prefix for resources"
  type        = string
  default     = "en-garde"
}

variable "lambda_memory_size" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "secret_key" {
  description = "Flask SECRET_KEY for session signing"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Custom domain for CloudFront"
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Route 53 zone ID for DNS validation and A record"
  type        = string
  default     = ""
}

variable "alert_email" {
  description = "Email address to receive CloudWatch alarm notifications (leave empty to skip SNS subscription)"
  type        = string
  default     = ""
}

variable "enable_xray" {
  description = "Enable AWS X-Ray active tracing on the Lambda function"
  type        = bool
  default     = true
}

variable "ses_from_email" {
  description = "Verified SES email address used as the sender for registration confirmation emails"
  type        = string
  default     = ""
}

variable "registration_queue_arn" {
  description = "Internal — populated from aws_sqs_queue.registration.arn (used by IAM policies)"
  type        = string
  default     = ""
}
