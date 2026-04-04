variable "aws_region" {
  description = "AWS region for the state backend resources"
  type        = string
  default     = "eu-west-3"
}

variable "app_name" {
  description = "Application name used for tagging"
  type        = string
  default     = "phishing-app"
}

variable "state_bucket_name" {
  description = "S3 bucket name for Terraform state"
  type        = string
}

variable "lock_table_name" {
  description = "DynamoDB table name for Terraform state locking"
  type        = string
}
