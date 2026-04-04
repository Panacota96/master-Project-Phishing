# ─── AWS WAF v2 Web ACL ───────────────────────────────────────────────────────
# CloudFront-scoped WAF rules MUST be deployed in us-east-1.
# Uses the `aws.us_east_1` provider alias declared in main.tf.

resource "aws_wafv2_web_acl" "app" {
  count    = var.enable_waf ? 1 : 0
  provider = aws.us_east_1

  name  = "${local.prefix}-waf"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # ─── Rate-based rule: block IPs exceeding 300 requests / 5 min ───────────
  rule {
    name     = "RateLimitPerIP"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 300
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.prefix}-rate-limit"
      sampled_requests_enabled   = true
    }
  }

  # ─── Managed Rule: OWASP Top 10 (SQLi, XSS, etc.) ────────────────────────
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 10

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.prefix}-common-rules"
      sampled_requests_enabled   = true
    }
  }

  # ─── Managed Rule: Known bad inputs (Log4j, path traversal, etc.) ─────────
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 20

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.prefix}-bad-inputs"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.prefix}-waf"
    sampled_requests_enabled   = true
  }

  tags = {
    Name = "${local.prefix}-waf"
  }
}

# ─── Outputs ──────────────────────────────────────────────────────────────────

output "waf_web_acl_arn" {
  description = "ARN of the WAF v2 Web ACL attached to CloudFront (empty if WAF disabled)"
  value       = var.enable_waf ? aws_wafv2_web_acl.app[0].arn : ""
}
