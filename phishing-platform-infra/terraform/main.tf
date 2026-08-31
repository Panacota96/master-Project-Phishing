terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {}
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.app_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

data "aws_caller_identity" "current" {}

locals {
  prefix = "${var.app_name}-${var.environment}"

  # S3 bucket names are globally unique across all AWS accounts, so the bare
  # "<app>-<env>-<region>" name collides with buckets left behind by any other
  # account that ever ran this stack. Suffixing the account ID keeps the name
  # unique and lets the stack be rebuilt in a fresh account.
  bucket_name = "${local.prefix}-${var.aws_region}-${data.aws_caller_identity.current.account_id}"
}
