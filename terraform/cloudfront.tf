# ─── CloudFront Distribution ──────────────────────────────────────────────────
# Provides a stable dXXXXX.cloudfront.net URL that survives API Gateway
# destroy/recreate cycles. No custom domain or ACM certificate required.

resource "aws_cloudfront_distribution" "app" {
  enabled             = true
  comment             = "${local.prefix} – stable login URL"
  default_root_object = ""

  origin {
    domain_name = replace(aws_apigatewayv2_api.app.api_endpoint, "https://", "")
    origin_id   = "apigw"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "apigw"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "CloudFront-Forwarded-Proto"]
      cookies {
        forward = "all"
      }
    }

    # No caching — app is dynamic (login sessions, quiz state)
    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${local.prefix}-cf"
  }
}
