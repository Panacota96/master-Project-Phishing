# ─── CloudTrail — Audit Logging ──────────────────────────────────────────────
# Multi-region trail capturing all management events and S3 data events
# for the application bucket. Logs go to a dedicated encrypted S3 bucket.

data "aws_caller_identity" "current" {}

# ─── Dedicated S3 Bucket for Trail Logs ──────────────────────────────────────

resource "aws_s3_bucket" "cloudtrail" {
  count         = var.enable_cloudtrail ? 1 : 0
  bucket        = "${local.prefix}-cloudtrail-${data.aws_caller_identity.current.account_id}"
  force_destroy = var.cloudtrail_bucket_force_destroy

  tags = {
    Name = "${local.prefix}-cloudtrail"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail" {
  count  = var.enable_cloudtrail ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "cloudtrail" {
  count  = var.enable_cloudtrail ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "cloudtrail" {
  count  = var.enable_cloudtrail ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail[0].arn
        Condition = {
          StringEquals = {
            "aws:SourceArn" = "arn:aws:cloudtrail:${var.aws_region}:${data.aws_caller_identity.current.account_id}:trail/${local.prefix}-trail"
          }
        }
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail[0].arn}/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl"  = "bucket-owner-full-control"
            "aws:SourceArn" = "arn:aws:cloudtrail:${var.aws_region}:${data.aws_caller_identity.current.account_id}:trail/${local.prefix}-trail"
          }
        }
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.cloudtrail]
}

# ─── CloudTrail Trail ─────────────────────────────────────────────────────────

resource "aws_cloudtrail" "app" {
  count = var.enable_cloudtrail ? 1 : 0
  name  = "${local.prefix}-trail"

  s3_bucket_name                = aws_s3_bucket.cloudtrail[0].id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true

  # Capture all S3 object-level events on the application bucket
  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::S3::Object"
      values = ["${aws_s3_bucket.app.arn}/"]
    }
  }

  tags = {
    Name = "${local.prefix}-trail"
  }

  depends_on = [aws_s3_bucket_policy.cloudtrail]
}

# ─── Outputs ──────────────────────────────────────────────────────────────────

output "cloudtrail_bucket" {
  description = "S3 bucket name for CloudTrail logs (empty if CloudTrail disabled)"
  value       = var.enable_cloudtrail ? aws_s3_bucket.cloudtrail[0].id : ""
}
