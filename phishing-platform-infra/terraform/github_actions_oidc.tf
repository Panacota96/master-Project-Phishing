resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1", "1c58a3a8518e8759bf075b76b750d4f2df264fcd"]
}

resource "aws_iam_role" "github_actions_deploy" {
  name = "${local.prefix}-github-actions-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:Panacota96/master-Project-Phishing:*"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "github_actions_deploy" {
  name = "${local.prefix}-github-actions-deploy"
  role = aws_iam_role.github_actions_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "LambdaCRUD"
        Effect = "Allow"
        Action = [
          "lambda:CreateFunction",
          "lambda:DeleteFunction",
          "lambda:GetFunction",
          "lambda:GetFunctionConfiguration",
          "lambda:ListVersionsByFunction",
          "lambda:PublishVersion",
          "lambda:UpdateFunctionCode",
          "lambda:UpdateFunctionConfiguration",
          "lambda:AddPermission",
          "lambda:RemovePermission",
          "lambda:GetPolicy",
          "lambda:CreateEventSourceMapping",
          "lambda:DeleteEventSourceMapping",
          "lambda:GetEventSourceMapping",
          "lambda:UpdateEventSourceMapping",
          "lambda:ListEventSourceMappings",
          "lambda:GetFunctionCodeSigningConfig",
          "lambda:TagResource",
          "lambda:UntagResource",
          "lambda:ListTags",
        ]
        Resource = "*"
      },
      {
        Sid    = "IAMRoleManagement"
        Effect = "Allow"
        Action = [
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:GetRole",
          "iam:TagRole",
          "iam:PassRole",
          "iam:ListInstanceProfilesForRole",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:GetRolePolicy",
          "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies",
          "iam:CreateOpenIDConnectProvider",
          "iam:DeleteOpenIDConnectProvider",
          "iam:GetOpenIDConnectProvider",
          "iam:UpdateOpenIDConnectProviderThumbprint",
          "iam:TagOpenIDConnectProvider",
        ]
        Resource = "*"
      },
      {
        Sid    = "DynamoDB"
        Effect = "Allow"
        Action = [
          "dynamodb:CreateTable",
          "dynamodb:DescribeTable",
          "dynamodb:DeleteTable",
          "dynamodb:UpdateTable",
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:BatchGetItem",
          "dynamodb:DescribeTimeToLive",
          "dynamodb:UpdateTimeToLive",
          "dynamodb:UpdateContinuousBackups",
          "dynamodb:ListTagsOfResource",
          "dynamodb:TagResource",
          "dynamodb:DescribeContinuousBackups",
        ]
        Resource = [
          "arn:aws:dynamodb:*:*:table/${local.prefix}-*",
          "arn:aws:dynamodb:*:*:table/phishing-terraform-locks",
        ]
      },
      {
        Sid    = "S3Full"
        Effect = "Allow"
        Action = "s3:*"
        Resource = [
          "arn:aws:s3:::${local.prefix}-*",
          "arn:aws:s3:::${local.prefix}-*/*",
          "arn:aws:s3:::phishing-terraform-state",
          "arn:aws:s3:::phishing-terraform-state/*",
        ]
      },
      {
        Sid      = "APIGateway"
        Effect   = "Allow"
        Action   = "apigateway:*"
        Resource = "*"
      },
      {
        Sid    = "CloudFront"
        Effect = "Allow"
        Action = [
          "cloudfront:CreateDistribution",
          "cloudfront:DeleteDistribution",
          "cloudfront:GetDistribution",
          "cloudfront:GetDistributionConfig",
          "cloudfront:UpdateDistribution",
          "cloudfront:ListDistributions",
          "cloudfront:TagResource",
          "cloudfront:UntagResource",
          "cloudfront:ListTagsForResource",
        ]
        Resource = "*"
      },
      {
        Sid    = "SecretsManager"
        Effect = "Allow"
        Action = [
          "secretsmanager:CreateSecret",
          "secretsmanager:DeleteSecret",
          "secretsmanager:DescribeSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:ListSecretVersionIds",
          "secretsmanager:PutSecretValue",
          "secretsmanager:TagResource",
          "secretsmanager:UntagResource",
          "secretsmanager:UpdateSecret",
        ]
        Resource = "*"
      },
      {
        Sid    = "CloudTrail"
        Effect = "Allow"
        Action = [
          "cloudtrail:AddTags",
          "cloudtrail:CreateTrail",
          "cloudtrail:DeleteTrail",
          "cloudtrail:DescribeTrails",
          "cloudtrail:GetTrail",
          "cloudtrail:GetTrailStatus",
          "cloudtrail:ListTags",
          "cloudtrail:RemoveTags",
          "cloudtrail:StartLogging",
          "cloudtrail:StopLogging",
          "cloudtrail:UpdateTrail",
        ]
        Resource = "*"
      },
      {
        Sid    = "WAFv2"
        Effect = "Allow"
        Action = [
          "wafv2:CreateWebACL",
          "wafv2:DeleteWebACL",
          "wafv2:GetWebACL",
          "wafv2:ListTagsForResource",
          "wafv2:ListWebACLs",
          "wafv2:TagResource",
          "wafv2:UntagResource",
          "wafv2:UpdateWebACL",
        ]
        Resource = "*"
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:DeleteLogGroup",
          "logs:PutRetentionPolicy",
          "logs:TagLogGroup",
          "logs:ListTagsLogGroup",
          "logs:ListLogDeliveries",
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws/*"
      },
      {
        Sid      = "CloudWatchLogsDescribe"
        Effect   = "Allow"
        Action   = ["logs:DescribeLogGroups", "logs:ListTagsForResource"]
        Resource = "*"
      },
      {
        Sid    = "CloudWatchLogDelivery"
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
        ]
        Resource = "*"
      },
      {
        Sid    = "ACMAndRoute53"
        Effect = "Allow"
        Action = [
          "acm:RequestCertificate",
          "acm:DescribeCertificate",
          "acm:DeleteCertificate",
          "acm:ListCertificates",
          "acm:AddTagsToCertificate",
          "route53:ChangeResourceRecordSets",
          "route53:GetChange",
          "route53:ListHostedZones",
          "route53:ListResourceRecordSets",
        ]
        Resource = "*"
      },
      {
        Sid    = "CloudWatchAlarmsDashboards"
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricAlarm",
          "cloudwatch:DeleteAlarms",
          "cloudwatch:DescribeAlarms",
          "cloudwatch:ListTagsForResource",
          "cloudwatch:PutDashboard",
          "cloudwatch:DeleteDashboards",
          "cloudwatch:GetDashboard",
        ]
        Resource = "*"
      },
      {
        Sid    = "SNS"
        Effect = "Allow"
        Action = [
          "sns:CreateTopic",
          "sns:DeleteTopic",
          "sns:Subscribe",
          "sns:Unsubscribe",
          "sns:GetTopicAttributes",
          "sns:SetTopicAttributes",
          "sns:ListTagsForResource",
          "sns:TagResource",
          "sns:GetSubscriptionAttributes",
          "sns:ListSubscriptionsByTopic",
        ]
        Resource = "*"
      },
      {
        Sid    = "SQS"
        Effect = "Allow"
        Action = [
          "sqs:CreateQueue",
          "sqs:DeleteQueue",
          "sqs:GetQueueAttributes",
          "sqs:SetQueueAttributes",
          "sqs:TagQueue",
          "sqs:GetQueueUrl",
          "sqs:ListQueueTags",
        ]
        Resource = "*"
      },
      {
        Sid    = "SES"
        Effect = "Allow"
        Action = [
          "ses:VerifyEmailIdentity",
          "ses:VerifyDomainIdentity",
          "ses:GetIdentityVerificationAttributes",
          "ses:DeleteIdentity",
          "ses:SetIdentityNotificationTopic",
          "ses:GetSendQuota",
          "ses:ListIdentities",
        ]
        Resource = "*"
      },
      {
        Sid    = "XRay"
        Effect = "Allow"
        Action = [
          "xray:CreateGroup",
          "xray:DeleteGroup",
          "xray:GetGroup",
          "xray:UpdateGroup",
        ]
        Resource = "*"
      },
    ]
  })
}

output "github_actions_deploy_role_arn" {
  description = "IAM role ARN to set as AWS_DEPLOY_ROLE_ARN secret in GitHub"
  value       = aws_iam_role.github_actions_deploy.arn
}
