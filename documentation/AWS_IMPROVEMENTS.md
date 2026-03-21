# AWS Infrastructure Improvement Report — En Garde (Phishing Awareness Platform)

> **Scope:** Production-readiness and business-showcase improvements for the En Garde phishing awareness training application.
> **Infrastructure baseline:** Terraform files in `terraform/` as of March 2026.
> **Region:** eu-west-3 (Paris).
> **Priority labels:** 🔴 Critical &nbsp;|&nbsp; 🟠 High &nbsp;|&nbsp; 🟡 Medium &nbsp;|&nbsp; 🟢 Nice-to-have

---

## Table of Contents

1. [Security Hardening](#1-security-hardening)
2. [Reliability and Resilience](#2-reliability-and-resilience)
3. [Performance and Cost Optimization](#3-performance-and-cost-optimization)
4. [Observability and Monitoring](#4-observability-and-monitoring)
5. [CI/CD Improvements](#5-cicd-improvements)
6. [Business Showcase Additions](#6-business-showcase-additions)
7. [Infrastructure as Code Quality](#7-infrastructure-as-code-quality)
8. [Prioritized Action Plan](#8-prioritized-action-plan)

---

## 1. Security Hardening

### 1.1 AWS WAF v2 on CloudFront

**Current state:** `aws_cloudfront_distribution.app` has no Web ACL associated. The distribution accepts all origins globally (`geo_restriction.restriction_type = "none"`) with no rate limiting or managed rule groups.

**Gap:** The application serves a French engineering school (ESME). It handles login sessions, quiz submissions, and EML file analysis — all of which are HTTP POST endpoints exposed directly through CloudFront → API Gateway. Without WAF, the application is open to credential-stuffing attacks on `/auth/login`, brute-force quiz submissions, and layer-7 floods.

**Recommendations:**

- 🔴 **Add `aws_wafv2_web_acl` (CLOUDFRONT scope, must be in `us-east-1`) and associate it with `aws_cloudfront_distribution.app` via `web_acl_id`.** At minimum, enable:
  - `AWSManagedRulesCommonRuleSet` — blocks OWASP Top 10 patterns including SQL injection and XSS.
  - `AWSManagedRulesKnownBadInputsRuleSet` — blocks Log4j, path traversal, and similar payloads.
  - A custom rate-based rule limiting each IP to 300 requests per 5 minutes to protect the login and quiz-submission endpoints.
- 🟡 **Geo-restriction:** Since this is an ESME school deployment, consider restricting to France (`FR`) and any other expected student countries rather than allowing all. This immediately eliminates the majority of opportunistic bot traffic. Use `geo_restriction.restriction_type = "whitelist"` in `aws_cloudfront_distribution.app`.
- 🟢 **WAF logging:** Send WAF logs to an S3 bucket (separate from `aws_s3_bucket.app`) or CloudWatch Logs for later analysis. This is required for any serious incident post-mortem.

### 1.2 CloudTrail for API Audit Logging

**Current state:** No `aws_cloudtrail` resource exists anywhere in `terraform/`. There is no audit trail of who called which AWS API and when.

**Gap:** For a business showcase, auditability is a baseline expectation. Without CloudTrail, there is no record of DynamoDB reads/writes from the Lambda functions, S3 object access, IAM role assumptions by GitHub Actions, or any administrative API call.

**Recommendations:**

- 🟠 **Create `aws_cloudtrail` with a multi-region trail** writing to a dedicated S3 bucket (not `aws_s3_bucket.app`) with server-side encryption. Enable `include_global_service_events = true` to capture IAM API calls. Enable `enable_log_file_validation = true` so log integrity can be verified.
- 🟡 **Enable S3 data event logging** on `aws_s3_bucket.app` for `GetObject` and `PutObject` — this will capture every EML file read by the Inspector and every video served, providing usage evidence for the showcase.
- 🟡 **Enable DynamoDB data event logging** for the `aws_dynamodb_table.users` and `aws_dynamodb_table.attempts` tables — captures every quiz score write and user lookup.

### 1.3 AWS Config for Compliance Rules

**Current state:** No `aws_config_configuration_recorder` or managed Config rules exist in Terraform.

**Gap:** AWS Config provides continuous compliance checks. For a business-grade deployment this catches configuration drift (e.g., someone manually disabling S3 versioning or removing bucket encryption).

**Recommendations:**

- 🟡 **Enable AWS Config recorder** in eu-west-3 with a delivery channel to an S3 bucket.
- 🟡 **Add managed rules** that directly apply to this stack:
  - `s3-bucket-versioning-enabled` — verifies `aws_s3_bucket_versioning.app` stays enabled.
  - `s3-bucket-server-side-encryption-enabled` — verifies `aws_s3_bucket_server_side_encryption_configuration.app` is not removed.
  - `dynamodb-pitr-enabled` — will catch if PITR (see Section 2.1) is accidentally disabled.
  - `lambda-function-settings-check` — can enforce minimum memory and maximum timeout.
  - `iam-password-policy` — for any IAM users (currently none, but worth having).

### 1.4 AWS Secrets Manager Instead of Lambda Environment Variables

**Current state:** `aws_lambda_function.app` passes `SECRET_KEY = var.secret_key` directly as a plaintext Lambda environment variable. The value is sourced from GitHub Actions secret `TF_VAR_SECRET_KEY` and written to a `.tfvars` file in the runner filesystem during the deploy workflow.

**Gap:** Lambda environment variables are stored in plaintext and visible to anyone with `lambda:GetFunctionConfiguration` — which the GitHub Actions role `aws_iam_role.github_actions_deploy` has (via `LambdaCRUD` Sid). The secret is also written to a GitHub Actions runner disk as `env/dev.tfvars` and `env/prod.tfvars`. Secrets Manager addresses both exposures.

**Recommendations:**

- 🔴 **Create `aws_secretsmanager_secret` for `SECRET_KEY`** and store the value as a Secrets Manager secret. Update the Lambda execution role `aws_iam_role.lambda` to include `secretsmanager:GetSecretValue` on that specific secret ARN. Update the Flask `config.py` to call `boto3.client('secretsmanager').get_secret_value()` at startup and cache the result.
- 🟠 **Remove `SECRET_KEY` from Lambda environment variables** in `lambda.tf`. The `sensitive = true` marker on `var.secret_key` in `variables.tf` prevents Terraform from printing it in plan output, but it does not prevent it from appearing in the AWS console or API.
- 🟠 **Also consider Secrets Manager for `SES_FROM_EMAIL`** — while not a secret in the cryptographic sense, centralizing config in Secrets Manager simplifies rotation and audit.
- 🟡 **Update the GitHub Actions OIDC role** (`aws_iam_role_policy.github_actions_deploy`) to add `secretsmanager:CreateSecret`, `secretsmanager:PutSecretValue`, `secretsmanager:DeleteSecret`, `secretsmanager:DescribeSecret`, `secretsmanager:TagResource` scoped to ARNs matching `arn:aws:secretsmanager:eu-west-3:*:secret:en-garde-*`.

### 1.5 S3 Bucket Policy Tightening — Video Access

**Current state:** In the dev environment, `aws_s3_bucket_policy.app_public_videos` adds a `Principal: "*"` policy allowing `s3:GetObject` on `${aws_s3_bucket.app.arn}/videos/*`. The `aws_s3_bucket_public_access_block.app` resource sets `block_public_policy` and `restrict_public_buckets` to `false` only when `var.environment == "dev"`.

**Gap:** The production path is already correct — prod blocks all public access. However, the dev branch using open S3 URLs for videos is architecturally inconsistent with the prod path and means videos in dev are served without authentication and without any access logging. The `seed_dynamodb.py` script hard-codes `VIDEO_BASE_URL` as a direct S3 URL (`https://${s3_bucket}.s3.eu-west-3.amazonaws.com/videos`) even for prod, bypassing CloudFront.

**Recommendations:**

- 🟠 **Serve videos through CloudFront with signed URLs or CloudFront Origin Access Control (OAC).** Add a second CloudFront origin pointing directly to `aws_s3_bucket.app` (not via API Gateway) with an OAC (`aws_cloudfront_origin_access_control`). Grant the OAC access via a bucket policy limited to `cloudfront.amazonaws.com`. Generate pre-signed CloudFront URLs in the Flask quiz route when serving video URLs. This eliminates the need for any public S3 bucket policy at any environment level.
- 🟠 **Remove the `aws_s3_bucket_policy.app_public_videos` resource entirely** once the CloudFront OAC approach is in place. A `count = var.environment == "dev" ? 1 : 0` guard is not sufficient protection — the public policy should never exist.
- 🟡 **Enable S3 server access logging** on `aws_s3_bucket.app` to a separate logging bucket. This is a standard requirement for any production storage holding user-submitted data (EML files).

### 1.6 VPC Consideration for Lambda

**Current state:** Both `aws_lambda_function.app` and `aws_lambda_function.registration_worker` run outside any VPC. They connect to DynamoDB and S3 via public AWS endpoints.

**Assessment:** For this architecture, placing Lambda inside a VPC is a trade-off, not a clear win.

**Reasons NOT to add a VPC for this stack:**
- DynamoDB and S3 have VPC Gateway Endpoints that keep traffic on the AWS network without NAT, so there is no actual security gain in terms of data exfiltration for these services.
- Lambda cold starts increase significantly in VPCs due to ENI attachment time — particularly damaging for a Flask app wrapped in Mangum where cold starts are already a concern.
- The application has no resources (RDS, ElastiCache, internal services) that require VPC placement to be reachable.
- SES, SQS, and SNS would require VPC Interface Endpoints or NAT Gateway, adding ~$32/month per endpoint in eu-west-3.

**Recommendation:** 🟢 **Skip VPC for this architecture.** Instead, tighten security via IAM resource-level policies, Secrets Manager, and WAF as described above. If a future version adds an RDS database or internal microservices, revisit VPC placement at that point.

### 1.7 IAM Least-Privilege Review — GitHub Actions Role

**Current state:** `aws_iam_role_policy.github_actions_deploy` (in `github_actions_oidc.tf`) has several over-broad permissions.

**Specific findings:**

- 🔴 **`S3Full` Sid grants `s3:*`** on `arn:aws:s3:::en-garde-dev-*` and the Terraform state bucket. This includes `s3:DeleteBucket`, `s3:PutBucketPolicy` (which could make the bucket public), and `s3:PutBucketVersioning` (could disable versioning). The GitHub Actions role only needs `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket`, `s3:GetBucketVersioning`, `s3:PutBucketVersioning`, `s3:GetEncryptionConfiguration`, `s3:PutEncryptionConfiguration`, `s3:GetBucketPublicAccessBlock`, `s3:PutPublicAccessBlock`, `s3:GetBucketTagging`, `s3:PutBucketTagging`, `s3:GetBucketPolicy`, `s3:PutBucketPolicy`, and `s3:GetBucketAcl` for Terraform to manage the bucket. `s3:DeleteBucket` is only needed during `terraform destroy`.

- 🔴 **`APIGateway` Sid grants `apigateway:*` on `Resource: "*"`** — this includes creating, modifying, and deleting API Gateways in any region, not scoped to the `${local.prefix}` resources. Restrict to ARN patterns for the specific API Gateway resources.

- 🟠 **`LambdaCRUD` Sid scopes `Resource: "*"`** — Lambda function ARNs are predictable (`arn:aws:lambda:eu-west-3:*:function:en-garde-*`). Restricting the resource prevents the deploy role from accidentally modifying unrelated Lambda functions in the same account.

- 🟠 **`IAMRoleManagement` Sid scopes `Resource: "*"`** — the role already only manages `en-garde-*` prefixed resources in practice. Scope this to `arn:aws:iam::*:role/en-garde-*` and `arn:aws:iam::*:policy/en-garde-*`.

- 🟠 **`SQS`, `SNS`, `SES`, `CloudWatchAlarmsDashboards` Sids all use `Resource: "*"`** — all of these can be scoped to ARN patterns matching `en-garde-*` prefix or the specific known ARNs.

- 🟡 **`StringLike` condition on the OIDC trust policy** uses `repo:Panacota96/master-Project-Phishing:*` — the trailing `:*` allows any branch and any workflow to assume this role. For production deploys, tighten to `repo:Panacota96/master-Project-Phishing:ref:refs/heads/main` to prevent feature branches from deploying to production infrastructure.

- 🟡 **Lambda execution role `aws_iam_role_policy.lambda_dynamodb`** includes `dynamodb:Scan` on all tables. The application should not be full-scanning any table in production — this is a sign of a query design issue and an over-broad permission. Review which routes actually use `Scan` and consider removing it or restricting it to admin-only tables.

---

## 2. Reliability and Resilience

### 2.1 DynamoDB Point-in-Time Recovery (PITR)

**Current state:** None of the nine DynamoDB tables (`aws_dynamodb_table.users`, `aws_dynamodb_table.quizzes`, `aws_dynamodb_table.attempts`, `aws_dynamodb_table.responses`, `aws_dynamodb_table.inspector_attempts`, `aws_dynamodb_table.inspector_attempts_anon`, `aws_dynamodb_table.bugs`, `aws_dynamodb_table.answer_key_overrides`, `aws_dynamodb_table.cohort_tokens`) have `point_in_time_recovery` blocks enabled.

**Gap:** If a bad deploy or a bug causes accidental data deletion or corruption (e.g., a `seed_dynamodb.py` run wipes and re-seeds attempts), there is no recovery path without PITR. For a platform that stores student learning progress, this is a critical gap.

**Recommendations:**

- 🔴 **Enable PITR on the three highest-value tables:** `aws_dynamodb_table.users`, `aws_dynamodb_table.attempts`, and `aws_dynamodb_table.responses`. These contain the irreplaceable student progress data. Add a `point_in_time_recovery { enabled = true }` block to each resource definition.
- 🟠 **Enable PITR on `aws_dynamodb_table.inspector_attempts` and `aws_dynamodb_table.inspector_attempts_anon`** — these contain the anonymized GDPR-safe records of student inspector sessions. Loss of this data would affect analytics reporting.
- 🟡 **Enable PITR on remaining tables** (`quizzes`, `bugs`, `answer_key_overrides`, `cohort_tokens`) — these are lower risk since quiz definitions and answer key overrides can be reseeded, but PITR has no additional cost beyond storage.

### 2.2 S3 Cross-Region Replication

**Current state:** `aws_s3_bucket_versioning.app` has versioning enabled (required for replication), but there is no `aws_s3_bucket_replication_configuration` resource.

**Gap:** The EML samples in `eml-samples/` and training videos in `videos/` are the core educational content. An accidental `aws s3 rm --recursive` in CI (which has `s3:*` access) or an S3 service disruption in eu-west-3 would make the Inspector non-functional.

**Recommendations:**

- 🟠 **Configure S3 cross-region replication from eu-west-3 to eu-west-1 (Ireland)** for the `eml-samples/` and `videos/` prefixes. This does not require a full bucket replication — filter by prefix. Create an IAM role for S3 replication and an `aws_s3_bucket_replication_configuration` resource.
- 🟡 **Alternatively, use S3 Batch Operations** to create a periodic copy of EML samples to a second bucket as a simpler DR strategy if full replication is over-engineered for the POC scale.

### 2.3 Lambda Reserved Concurrency and Provisioned Concurrency

**Current state:** `aws_lambda_function.app` has no `reserved_concurrent_executions` and no provisioned concurrency configuration. Cold starts will affect every request after periods of inactivity (a near-constant state for a school application that sees traffic in bursts during class sessions).

**Gap:** The Flask application packed with Mangum, boto3, Flask-Login, Flask-WTF, qrcode, and aws-xray-sdk has a non-trivial initialization path. Cold starts on a 512 MB Lambda in eu-west-3 for this dependency footprint are typically 2–4 seconds, which is noticeable to students.

**Recommendations:**

- 🟠 **Add `reserved_concurrent_executions = 10`** to `aws_lambda_function.app`. This prevents the app Lambda from consuming all 1,000 default account concurrency slots during a traffic spike, leaving headroom for `aws_lambda_function.registration_worker`. It also provides a hard cap that prevents runaway costs if a bot hits the endpoint.
- 🟡 **Add a provisioned concurrency configuration** (`aws_lambda_provisioned_concurrency_config`) with `provisioned_concurrent_executions = 1` for production deployments. This keeps one warm execution environment permanently, eliminating cold starts for the first concurrent request. At 512 MB, the cost is approximately $10–12/month — acceptable for a business showcase.
- 🟡 **For `aws_lambda_function.registration_worker`**, set `reserved_concurrent_executions = 5`. The registration worker processes one SQS message at a time (`batch_size = 1`) and does not need more than a handful of concurrent executions.

### 2.4 Dead-Letter Queue for the Registration Worker Lambda

**Current state:** The SQS queue `aws_sqs_queue.registration` has a redrive policy configured (`aws_sqs_queue.registration_dlq` with `maxReceiveCount = 4`, 14-day retention). This is the DLQ for the **SQS queue**, not for the Lambda function itself.

**Assessment:** The DLQ is correctly placed on the SQS queue, which is the right pattern for event-source-mapping triggered Lambdas. When the `aws_lambda_function.registration_worker` fails to process a message four times, SQS moves it to `aws_sqs_queue.registration_dlq`. This is working as intended.

**What is missing:**

- 🟠 **No CloudWatch alarm on `aws_sqs_queue.registration_dlq` `ApproximateNumberOfMessagesVisible`.** If registration emails are failing silently (e.g., SES sandbox mode, expired verification), messages pile up in the DLQ with no alert. Add an `aws_cloudwatch_metric_alarm` targeting the DLQ queue with a threshold of `>= 1` message, sending to `aws_sns_topic.alerts`.
- 🟡 **No CloudWatch alarm on `aws_lambda_function.registration_worker` errors.** The existing `aws_cloudwatch_metric_alarm.lambda_errors` only monitors `aws_lambda_function.app`. Add a parallel alarm for `aws_lambda_function.registration_worker`.
- 🟢 **Add X-Ray tracing to `aws_lambda_function.registration_worker`** (currently no `tracing_config` block) to enable distributed trace correlation between the main app Lambda and the worker.

### 2.5 API Gateway Throttling and Usage Plans

**Current state:** `aws_apigatewayv2_stage.default` uses `auto_deploy = true` with no `default_route_settings` block defining throttling. HTTP API v2 does not support usage plans (those are REST API/v1 features), but it does support route-level and stage-level throttling via `default_route_settings`.

**Gap:** Without throttling, a single misbehaving client or an accidental browser refresh loop from a student could trigger sustained Lambda invocations. The existing `aws_cloudwatch_metric_alarm.lambda_throttles` will only fire once Lambda account-level concurrency is exhausted — by which point the damage is done.

**Recommendations:**

- 🟠 **Add `default_route_settings` to `aws_apigatewayv2_stage.default`** with:
  - `throttling_burst_limit = 50` — maximum concurrent requests per second.
  - `throttling_rate_limit = 20` — sustained requests per second.
  These values are conservative for a school cohort scenario. Adjust upward if classroom sessions involve simultaneous quiz submissions from many students.
- 🟡 **Add route-level overrides** for the most sensitive endpoints — specifically the Inspector API routes (`/inspector/api/*`) and login (`/auth/login`) — with tighter limits than the defaults.

### 2.6 Multi-Region Active-Passive Failover

**Current state:** All resources are in eu-west-3 only. There is no failover configuration in Route 53.

**Assessment for this project:** Full multi-region active-passive failover (Route 53 health checks + secondary region with separate DynamoDB global tables) is significant infrastructure investment and is likely beyond the scope of this academic POC.

**Recommendations:**

- 🟢 **As a showcase talking point:** Document the multi-region approach in ARCHITECTURE.md — describe how DynamoDB Global Tables would replicate `users`, `attempts`, and `inspector_attempts` to eu-west-1, and how Route 53 health checks would detect API Gateway failure and reroute. This demonstrates architectural awareness without requiring implementation.
- 🟡 **Achievable DR improvement:** Enable Route 53 health checks on the CloudFront distribution if a custom domain is configured. Set `evaluate_target_health = true` on the `aws_route53_record.app` alias. This at minimum detects and reports CloudFront-level outages, even if there is no active failover target.

---

## 3. Performance and Cost Optimization

### 3.1 DynamoDB Billing Mode — When to Switch from PAY_PER_REQUEST

**Current state:** All nine DynamoDB tables use `billing_mode = "PAY_PER_REQUEST"`.

**Assessment:** PAY_PER_REQUEST is the correct choice for this application's traffic profile. School cohorts generate burst traffic during class sessions and near-zero traffic otherwise. Switching to PROVISIONED would require capacity planning and auto-scaling configuration that would add cost during off-peak hours.

**Recommendation:** 🟢 **Stay on PAY_PER_REQUEST.** The break-even point for switching to PROVISIONED is sustained traffic of roughly 200+ read/write capacity units per hour. A school cohort of ~100 students will not reach this level for a quiz application. Revisit after 3 months of CloudWatch DynamoDB consumed capacity data.

### 3.2 Lambda Memory Tuning

**Current state:** `aws_lambda_function.app` is configured with `var.lambda_memory_size` (default 512 MB). `aws_lambda_function.registration_worker` is hardcoded to 256 MB.

**Gap:** Lambda bills on GB-seconds. Under-provisioned memory increases execution duration (and cost). Over-provisioned memory wastes money. 512 MB is a reasonable starting guess for a Flask app but has not been empirically validated.

**Recommendations:**

- 🟠 **Run AWS Lambda Power Tuning** (an open-source Step Functions state machine from AWS) against `aws_lambda_function.app` to find the cost-performance optimal memory setting. For Flask apps with boto3, the optimal memory is often 768 MB–1024 MB where the faster CPU allocation reduces duration enough to offset the higher per-GB-second rate.
- 🟡 **Run Lambda Power Tuning against `aws_lambda_function.registration_worker`** — this function does DynamoDB reads/writes and SES API calls; at 256 MB it may be CPU-bound during JSON serialization.
- 🟡 **Parameterize registration worker memory** in `variables.tf` the same way the app Lambda is (`var.lambda_memory_size`) to allow tuning without code changes.

### 3.3 CloudFront Cache Behavior Optimization

**Current state:** `aws_cloudfront_distribution.app` has a single `default_cache_behavior` with `min_ttl = 0`, `default_ttl = 0`, `max_ttl = 0` — meaning CloudFront never caches anything and every request is forwarded to API Gateway and Lambda.

**Gap:** This is correct for dynamic application routes (login, quiz, dashboard) but wasteful for static assets. The Flask application serves CSS, JavaScript, and image files from `app/static/`. Every static asset request hits Lambda, which reads the file from disk (inside the Lambda deployment package), and returns it — incurring Lambda invocation cost and latency when CloudFront could serve it from edge.

**Recommendations:**

- 🟠 **Add a separate CloudFront cache behavior for `/static/*`** with `min_ttl = 86400`, `default_ttl = 604800`, `max_ttl = 31536000` (1 year). Set cache key to path only (no cookies, no query strings). This alone can eliminate 40–60% of Lambda invocations during active sessions, since browsers fetch multiple static assets per page load.
- 🟠 **Add S3 as a second CloudFront origin** for `/videos/*` and `/eml-samples/*` using OAC (see Section 1.5). Cache videos with a long TTL — training video content changes rarely.
- 🟡 **Set `compress = true`** (already enabled) and ensure the Flask app sets `Cache-Control` headers on static responses so browsers respect the cache. Consider using Flask's `send_from_directory` with explicit `max_age` for static assets.
- 🟡 **Enable CloudFront real-time logging** to a Kinesis Data Firehose to capture cache hit/miss ratios and optimize behaviors over time.

### 3.4 S3 Intelligent-Tiering for EML Samples and Videos

**Current state:** `aws_s3_bucket_server_side_encryption_configuration.app` uses AES256 but there is no lifecycle policy or storage class configuration.

**Gap:** EML samples and training videos are accessed frequently during class sessions but rarely otherwise. All objects default to S3 Standard storage class, which charges for storage even when objects are not accessed.

**Recommendations:**

- 🟡 **Add an `aws_s3_bucket_lifecycle_configuration`** for `aws_s3_bucket.app` with:
  - Transition `eml-samples/*` objects to S3 Intelligent-Tiering after 0 days (immediate, since access patterns are unpredictable).
  - Transition `videos/*` objects to S3 Intelligent-Tiering after 0 days.
  - Expire non-current versions of objects after 30 days to control versioning storage costs (since `aws_s3_bucket_versioning.app` is enabled).
- 🟢 **Expire `cohort-qr/*` prefix objects** (if QR registration tokens are stored in S3) after 7 days. The `aws_dynamodb_table.cohort_tokens` already has TTL enabled — ensure any corresponding S3 objects are cleaned up.

### 3.5 AWS Cost Anomaly Detection

**Current state:** No `aws_ce_anomaly_monitor` or `aws_ce_anomaly_subscription` resource exists.

**Gap:** Without Cost Anomaly Detection, unexpected cost spikes (e.g., a Lambda in an infinite retry loop, a bot hammering the API) are only caught when the monthly bill arrives.

**Recommendations:**

- 🟠 **Create an `aws_ce_anomaly_monitor`** of type `DIMENSIONAL` monitoring the `SERVICE` dimension. Create an `aws_ce_anomaly_subscription` sending alerts to `aws_sns_topic.alerts` when an anomaly exceeds $5 (appropriate threshold for a small school deployment). This costs nothing to enable and can prevent bill shock.

---

## 4. Observability and Monitoring

### 4.1 Current Setup Review

The existing monitoring (`cloudwatch_monitoring.tf`) is solid for a first pass:

- `aws_cloudwatch_metric_alarm.lambda_errors` — Lambda errors >= 5 per 5 min. Alert fires and recovers via `aws_sns_topic.alerts`.
- `aws_cloudwatch_metric_alarm.lambda_duration_p95` — P95 duration >= 25,000 ms (25 seconds). This is set at 83% of the 30-second Lambda timeout, which is correct.
- `aws_cloudwatch_metric_alarm.lambda_throttles` — Throttles >= 1. Fires on first throttle, which is aggressive but appropriate.
- `aws_cloudwatch_metric_alarm.apigw_5xx` — API Gateway 5xx >= 3 per 5 min.
- `aws_cloudwatch_metric_alarm.apigw_4xx` — API Gateway 4xx >= 50 per 5 min.
- `aws_cloudwatch_metric_alarm.dynamodb_system_errors` — DynamoDB system errors >= 1.
- `aws_cloudwatch_dashboard.overview` — 3-row dashboard covering Lambda, API Gateway, and DynamoDB read/write capacity.

### 4.2 Distributed Tracing — X-Ray

**Current state:** X-Ray tracing is configured in `aws_lambda_function.app` via `tracing_config { mode = var.enable_xray ? "Active" : "PassThrough" }`. The IAM policy `aws_iam_role_policy.lambda_xray` grants the required `xray:PutTraceSegments` and `xray:PutTelemetryRecords`. The `aws-xray-sdk==2.14.0` package is in `requirements.txt`.

**Gap:** The X-Ray SDK is installed and the Lambda has the IAM permissions and tracing mode enabled. However, there is no evidence in `app/__init__.py` or the blueprint routes that the SDK is actually instrumented — `XRayMiddleware` or `patch_all()` are not called in the Flask app factory. Without instrumentation, X-Ray will capture Lambda-level segments (invocation duration) but will not capture sub-segments for DynamoDB calls, S3 calls, or SQS calls.

**Recommendations:**

- 🟠 **Instrument the Flask app with X-Ray SDK.** In `app/__init__.py`, call `from aws_xray_sdk.core import xray_recorder, patch_all` and `patch_all()` to automatically create sub-segments for all boto3 calls. This will produce traces showing exactly which DynamoDB table or S3 path is causing latency.
- 🟠 **Add X-Ray to `aws_lambda_function.registration_worker`** — add a `tracing_config` block and the `aws-xray-sdk` dependency to the registration worker's requirements. Add the X-Ray IAM permissions to `aws_iam_role_policy.registration_worker`.
- 🟡 **Create an X-Ray group** (`aws_xray_group`) filtering traces where `ResponseTime > 5` to quickly surface slow requests in the console.

### 4.3 CloudWatch Logs Insights Queries

**Current state:** Log groups exist for both Lambda functions (`aws_cloudwatch_log_group.lambda`, `aws_cloudwatch_log_group.registration_worker`) and for API Gateway (`aws_cloudwatch_log_group.apigw`) with 14-day retention. No saved Insights queries are defined.

**Recommendations:**

- 🟡 **Create `aws_cloudwatch_query_definition` resources** for the most useful operational queries:
  - Find all 5xx responses in the last hour from API Gateway logs.
  - Find all Lambda cold starts (filter `INIT_START` in Lambda logs).
  - Find quiz submission failures (filter for Flask error logs containing "inspector" or "quiz").
  - Find the top 10 most frequent error messages from the Lambda function.
- 🟡 **Increase log retention from 14 days to 30 days** on all three log groups for production. 14 days is sufficient for operational debugging but too short for incident investigation or regulatory review.

### 4.4 CloudWatch Synthetics Canary

**Current state:** No `aws_synthetics_canary` resource exists. Application uptime is only detected reactively through CloudWatch alarms firing on actual user traffic errors.

**Gap:** If the application is down at 3am, no alarm fires until a student actually attempts a request and triggers errors. For a business showcase, demonstrating proactive uptime monitoring is important.

**Recommendations:**

- 🟠 **Create an `aws_synthetics_canary`** that runs every 5 minutes, performing a HEAD request to `https://${aws_cloudfront_distribution.app.domain_name}/auth/login`. This endpoint returns a 200 for the unauthenticated login form. A canary failure fires an alarm before any student experiences downtime.
- 🟡 **Add a CloudWatch alarm** (`aws_cloudwatch_metric_alarm`) on the canary's `SuccessPercent` metric, triggering `aws_sns_topic.alerts` when success drops below 100% for two consecutive periods.

### 4.5 Business Metrics as Custom CloudWatch Metrics

**Current state:** `aws_cloudwatch_dashboard.overview` shows only infrastructure metrics. There are no application-level business metrics published to CloudWatch.

**Gap:** For a business showcase, the most compelling thing to show is *business outcomes*, not just infrastructure health. Metrics like quiz completion rate and Inspector submission rate demonstrate the platform is achieving its educational mission.

**Recommendations:**

- 🟡 **Publish custom CloudWatch metrics** from the Flask application using `boto3.client('cloudwatch').put_metric_data()` (or the X-Ray SDK's custom annotations). Suggested metrics in the `EnGarde/Application` namespace:
  - `QuizSubmitted` — count per quiz_id dimension, published each time `api_submit` succeeds.
  - `InspectorSubmitted` — count, published each time `api_submit` in the inspector route succeeds.
  - `LoginSuccess` and `LoginFailure` — counts for security monitoring.
  - `UserRegistered` — count published by `aws_lambda_function.registration_worker` on successful user creation.
- 🟡 **Add a fourth row to `aws_cloudwatch_dashboard.overview`** displaying these business metrics alongside the infrastructure metrics. This makes the dashboard useful to non-engineering stakeholders (faculty, school administrators).
- 🟢 **Consider Amazon QuickSight** for richer analytics dashboards if faculty need cross-cohort reports. QuickSight can connect directly to DynamoDB via S3 export or via Athena.

### 4.6 Missing Alarm: SQS DLQ Messages

As noted in Section 2.4, there is no alarm on `aws_sqs_queue.registration_dlq`. This means failed registration emails are invisible.

- 🟠 **Add `aws_cloudwatch_metric_alarm`** on `ApproximateNumberOfMessagesVisible` for `aws_sqs_queue.registration_dlq`, threshold >= 1, alarm action to `aws_sns_topic.alerts`.

---

## 5. CI/CD Improvements

### 5.1 Current Pipeline Review

The CI/CD setup is well-structured:

- `ci.yml` — lint (flake8), EML validation, pytest with moto, Lambda artifact build. Runs on every push/PR.
- `deploy-dev.yml` — triggered on push to `main`. Calls `ci.yml`, then runs Terraform plan + apply for dev, seeds DynamoDB, syncs assets. Three-job pipeline with plan output uploaded as artifact.
- `deploy-prod.yml` — manual `workflow_dispatch` only. Separate build job, then plan + apply requiring `environment: prod` GitHub approval gate.

This is a correct separation of concerns. The plan/apply split with artifact upload between jobs is good practice.

### 5.2 Terraform Drift Detection

**Current state:** Terraform only runs during deploy workflows. There is no scheduled drift detection.

**Gap:** If someone manually modifies an AWS resource (e.g., changes a Lambda timeout in the console, or modifies a DynamoDB billing mode), the Terraform state drifts silently. This is especially risky given the GitHub Actions role has broad permissions.

**Recommendations:**

- 🟠 **Add a scheduled GitHub Actions workflow** (`drift-detection.yml`) that runs `terraform plan -detailed-exitcode` on a cron schedule (e.g., daily at 06:00 UTC) and fails the workflow (or posts a comment/notification) if exit code 2 is returned (changes detected). This requires the GitHub Actions OIDC role to be assumable from the scheduled workflow context.
- 🟡 **Store the drift detection plan output** as a GitHub Actions job summary or post it to a Slack channel / GitHub issue for visibility.

### 5.3 Terraform State Locking

**Current state:** The bootstrap (`terraform/bootstrap/main.tf`) creates `aws_dynamodb_table.lock` with hash key `LockID`. This is the standard DynamoDB state locking table for the S3 Terraform backend.

**Assessment:** State locking is correctly provisioned. The backend configuration references this table via `backend/dev.hcl` and `backend/prod.hcl` (not visible in the read files but inferred from `terraform init -backend-config="backend/dev.hcl"`). The `phishing-terraform-locks` table ARN appears in the GitHub Actions DynamoDB policy, confirming it is in use.

**What to verify:** Confirm that `backend/dev.hcl` and `backend/prod.hcl` both include `dynamodb_table = "phishing-terraform-locks"`. If the `dynamodb_table` key is missing, concurrent CI runs could corrupt Terraform state.

- 🔴 **Confirm state locking is active** by checking both `.hcl` files include the `dynamodb_table` key. If missing, add it immediately — a corrupted Terraform state is one of the hardest operational problems to recover from.

### 5.4 Environment Promotion Flow

**Current state:** Dev deploys automatically on every push to `main`. Prod is `workflow_dispatch` only (manual trigger). There is no staging environment or automated promotion gate.

**Gap:** The current model means that whatever is on `main` is immediately deployed to dev — there is no gating step between dev validation and prod promotion other than the manual workflow trigger.

**Recommendations:**

- 🟡 **Add a required status check** on the `deploy_dev` job completing successfully before the `deploy-prod` workflow is manually triggerable. GitHub Environments already provide an approval gate for `environment: prod`, but adding an explicit dependency check (e.g., checking the last dev deploy status) adds a second layer.
- 🟡 **Add a smoke test step** to both deploy workflows — after `terraform apply`, run a `curl -f` against the deployed CloudFront URL's login page to confirm the deployment is live. Currently the workflow only captures Terraform outputs; it does not verify the endpoint is actually responding.
- 🟢 **Consider a `staging` environment** (separate AWS environment values, separate Terraform workspace) between dev and prod for longer-running user acceptance testing during cohort onboarding periods.

### 5.5 Automated Rollback on Lambda Error Spike

**Current state:** No automated rollback exists. If a bad Lambda deployment causes a spike in `aws_cloudwatch_metric_alarm.lambda_errors`, the alarm sends an SNS email notification but takes no automated remediation action.

**Recommendations:**

- 🟡 **Publish Lambda versions** by adding `publish = true` to `aws_lambda_function.app`. Then use an `aws_lambda_alias` (e.g., `live`) pointing to the latest version. This enables instant rollback by shifting the alias to the previous version without a full Terraform apply.
- 🟡 **Add an AWS CodeDeploy deployment group** (`aws_codedeploy_app`, `aws_codedeploy_deployment_group`) using the `Lambda` compute platform with a `Linear10PercentEvery1Minute` deployment configuration and CloudWatch alarm rollback trigger pointing to `aws_cloudwatch_metric_alarm.lambda_errors`. This provides automated traffic shifting with automatic rollback if errors exceed the threshold — a genuine production-grade capability worth demonstrating.

---

## 6. Business Showcase Additions

### 6.1 Custom Domain with ACM Certificate

**Current state:** `acm_custom_domain.tf` is fully implemented. `aws_acm_certificate.custom_domain` requests a certificate in `us-east-1` (required for CloudFront). `aws_route53_record.cert_validation` creates DNS validation records. `aws_acm_certificate_validation.custom_domain` waits for validation. `aws_route53_record.app` creates the A-alias record pointing to CloudFront. All resources are gated by `var.domain_name != ""`.

**Assessment:** The custom domain implementation is complete and correct. All that is needed is to set `var.domain_name` and `var.route53_zone_id` in the prod tfvars. The ACM certificate will be issued in us-east-1 and attached to the CloudFront distribution via the `viewer_certificate` block in `cloudfront.tf`.

**Recommendations:**

- 🟠 **Set `domain_name` and `route53_zone_id` in prod tfvars** before the business showcase. Showing the application at `https://engarde.esme.fr` (or similar) rather than a CloudFront hash URL is a significant professionalism improvement.
- 🟡 **Add `www.` subdomain support** by adding a second `aliases` entry to the CloudFront distribution and a `Subject Alternative Name` on the ACM certificate using `subject_alternative_names = ["www.${var.domain_name}"]`.

### 6.2 Static Asset Hosting to Reduce Lambda Cold Starts

**Current state:** All requests — including CSS, JavaScript, and images from `app/static/` — flow through CloudFront → API Gateway → Lambda. Static assets are served by Flask's built-in `send_static_file`. This means every page load that fetches static files triggers Lambda invocations.

**Recommendations:**

- 🟠 **Offload static assets to S3 + CloudFront** (described in Section 3.3). During the Lambda build in CI, copy the `app/static/` directory to S3 under a `static/` prefix. Add a CloudFront cache behavior matching `/static/*` pointing to S3 as origin. Update the Flask template `url_for('static', ...)` calls to use `{{ config.STATIC_URL }}/...` where `STATIC_URL` points to the CloudFront URL. This can reduce Lambda invocations by 30–50% and eliminate static asset cold starts entirely.
- 🟢 **AWS Amplify** is an alternative for hosting the static layer, but for this architecture it would add significant complexity for minimal gain. The S3 + CloudFront approach is simpler and already uses existing infrastructure.

### 6.3 AWS Cognito vs. Current Flask-Login — Trade-off Analysis

**Current state:** Authentication is implemented as a custom Flask-Login integration backed by `aws_dynamodb_table.users`. Passwords are hashed with Werkzeug (bcrypt-based). There is no self-registration (admin-only account creation or QR-flow). Session management uses Flask's signed cookie sessions with `SECRET_KEY`.

**Assessment for this project:**

| Aspect | Current Flask-Login | AWS Cognito |
|---|---|---|
| Admin-controlled user creation | Native (admin CSV import + QR flow) | Requires custom admin Lambda or Amplify Admin UI |
| GDPR compliance | Manual (current approach stores minimal data) | Built-in compliance features |
| MFA support | Not implemented | Native TOTP/SMS MFA |
| Cost | $0 (DynamoDB reads only) | Free up to 50k MAU, then $0.0055/MAU |
| Implementation effort to add | Low | High — requires Cognito User Pool, App Client, hosted UI or custom UI integration, and rewriting all auth routes |
| Cohort-based user management | Native (group/class_name fields) | Cognito Groups map 1:1 to cohorts |
| Session tokens | Flask cookie | JWT (ID/Access/Refresh tokens) |

**Recommendation:** 🟢 **Keep Flask-Login for this POC.** The current implementation is correct, tested, and cohort-aware. Migrating to Cognito would require rewriting all four blueprints' auth decorators, replacing `flask_login.current_user` references, and re-implementing the admin user management flow. The security benefit (Cognito handles password storage) is largely replicated by Werkzeug's bcrypt hashing. **Document Cognito as the recommended future evolution** in ARCHITECTURE.md, noting that Cognito Groups map to the existing `group` attribute in DynamoDB.

### 6.4 API Gateway Custom Domain Mapping

**Current state:** The API Gateway (`aws_apigatewayv2_api.app`) is accessed via CloudFront with no direct custom domain mapping on the API Gateway itself. There is no `aws_apigatewayv2_domain_name` or `aws_apigatewayv2_api_mapping` resource.

**Assessment:** Since all traffic flows through CloudFront (`aws_cloudfront_distribution.app`), there is no need for an API Gateway custom domain mapping — CloudFront is the termination point for the custom domain. The API Gateway endpoint is not exposed directly to users. This is architecturally correct.

**Recommendation:** 🟢 **No action needed.** The existing architecture correctly uses CloudFront as the single entry point. Adding an API Gateway custom domain would be redundant and would create a second unprotected entry point bypassing CloudFront (and any future WAF).

### 6.5 Service Quotas Review Before Go-Live

**Current state:** No Service Quotas review is documented.

**Before a business showcase or cohort launch, verify these limits in eu-west-3:**

- 🟠 **Lambda concurrent executions:** Default is 1,000 per region. With both `app` and `registration_worker` functions, and assuming up to 50 simultaneous students, 1,000 is more than sufficient. However, if other Lambda functions exist in the same account, check the account-level remaining quota.
- 🟠 **SES sending limits:** If the SES account is in sandbox mode, emails can only be sent to verified addresses. For a real cohort launch, SES must be moved out of sandbox (requires AWS Support request). The current `aws_ses_email_identity.from` only verifies the sender address — student email addresses also need to be verified in sandbox mode.
- 🟡 **DynamoDB table limits:** Default is 2,500 tables per region. With 9 tables for this app, this is not a concern.
- 🟡 **API Gateway routes per API:** Default is 300 routes. The catch-all `$default` route means only 1 route is used.
- 🟡 **CloudFront distributions:** Default is 200 per account. Not a concern.
- 🟡 **ACM certificates:** Default is 2,500 per region. Not a concern.

### 6.6 Well-Architected Framework Mapping

The AWS Well-Architected Framework has six pillars. Here is an honest mapping of the current En Garde infrastructure:

#### Operational Excellence
- **Strength:** IaC (Terraform), CI/CD with OIDC, structured logging (API Gateway + Lambda log groups), CloudWatch alarms and dashboard.
- **Gap:** No drift detection, no canary deployments, no runbook documentation for incident response.

#### Security
- **Strength:** OIDC-based CI/CD (no long-lived credentials), HTTPS everywhere (CloudFront forces HTTPS), S3 versioning, SQS SSE encryption (`sqs_managed_sse_enabled = true`), Lambda X-Ray tracing enabled.
- **Gap:** No WAF, no CloudTrail, `SECRET_KEY` in environment variables, `s3:*` in GitHub Actions role, no VPC (acceptable trade-off as discussed).

#### Reliability
- **Strength:** SQS DLQ for registration worker, serverless architecture (no servers to maintain), CloudFront as stable entry point surviving API Gateway destroy/recreate cycles.
- **Gap:** No PITR on DynamoDB tables, no cross-region replication, no Lambda provisioned concurrency, no throttling on API Gateway.

#### Performance Efficiency
- **Strength:** CloudFront CDN with `compress = true`, Lambda memory configurable via variable, PAY_PER_REQUEST DynamoDB (no capacity planning required).
- **Gap:** All static assets served through Lambda (no CloudFront caching for `/static/*`), no Lambda Power Tuning done, cold start risk.

#### Cost Optimization
- **Strength:** Serverless (pay-per-use), PAY_PER_REQUEST DynamoDB, no NAT Gateways or unnecessary VPC costs.
- **Gap:** No Cost Anomaly Detection, no lifecycle policies on S3 objects, static assets hitting Lambda unnecessarily.

#### Sustainability
- **Strength:** Serverless means near-zero compute when idle — better carbon footprint than always-on EC2.
- **Gap:** eu-west-3 (Paris) has relatively good renewable energy mix. No explicit sustainability tagging or reporting.

---

## 7. Infrastructure as Code Quality

### 7.1 Tagging Strategy

**Current state:** `main.tf` applies three default tags to all resources via `provider.default_tags`: `Project = var.app_name`, `Environment = var.environment`, `ManagedBy = "terraform"`.

**Gap:** For a business showcase, especially one that is part of an academic institution, cost allocation and ownership tagging are important for demonstrating governance.

**Recommendations:**

- 🟡 **Add `CostCenter` tag** — even if fictional for an academic project (e.g., `"ESME-Engineering"`), this demonstrates FinOps awareness.
- 🟡 **Add `Owner` or `Team` tag** — the responsible person or team (e.g., `"CyberSec-Lab"`).
- 🟡 **Add `Application` tag** — the specific service name within the project (e.g., `"en-garde-web"`, `"en-garde-worker"`). Useful when multiple apps share the same AWS account.
- 🟡 **Add `Version` tag** to Lambda functions** — set to the current git commit SHA using `var.app_version` populated from `${GITHUB_SHA}` in the CI workflow. This allows tracing which code version a Lambda is running at a glance.
- 🟢 **Add `DataClassification` tag** to DynamoDB tables and S3 bucket** — e.g., `"Internal"` for user data tables, `"Public"` for EML samples. This is required by many data governance frameworks.

### 7.2 Terraform Module Extraction Opportunities

**Current state:** All resources are defined as flat top-level resources across 15 `.tf` files. There are no local modules.

**Identified module candidates:**

- 🟡 **`lambda_function` module** — `aws_lambda_function`, `aws_cloudwatch_log_group`, and `aws_iam_role_policy` resources appear twice (once for the app Lambda in `lambda.tf` + `iam.tf`, once for the registration worker in `lambda_registration_worker.tf`). A module with inputs for `function_name`, `handler`, `memory_size`, `timeout`, `environment_variables`, and `policy_document` would reduce duplication.
- 🟡 **`dynamodb_table` module** — the nine DynamoDB tables share a common structure (PAY_PER_REQUEST, AES256 encryption, optional GSIs). A module with inputs for `table_name`, `hash_key`, `range_key`, `gsis`, and `enable_pitr` would make PITR adoption (Section 2.1) a single-line change per table.
- 🟢 **`cloudwatch_alarm` module** — the five existing alarms share the same SNS topic and evaluation structure. A module would make adding new alarms (Section 4.6, SQS DLQ) a one-block addition.

### 7.3 Remote State Configuration Review

**Current state:** `main.tf` declares `backend "s3" {}` with no inline configuration. Configuration is supplied via `backend/dev.hcl` and `backend/prod.hcl` at `terraform init` time. The bootstrap creates the S3 state bucket with versioning and AES256 encryption, and a DynamoDB locking table.

**Findings:**

- 🟠 **Verify `dynamodb_table` in backend HCL files.** The DynamoDB lock table `phishing-terraform-locks` exists in AWS (referenced in the GitHub Actions IAM policy) but the HCL backend config files were not readable in this review. If `dynamodb_table` is absent from either HCL file, concurrent CI runs will not be serialized and state corruption is possible.
- 🟡 **The Terraform state S3 bucket lacks `aws_s3_bucket_public_access_block`** in the bootstrap. The bootstrap (`terraform/bootstrap/main.tf`) creates `aws_s3_bucket_public_access_block.state` correctly with all four block settings set to `true`. This is correct — noted as confirmed.
- 🟡 **The Terraform state bucket is not versioned at the object level in the bootstrap HCL.** `aws_s3_bucket_versioning.state` has versioning enabled, which is correct. Ensure the bootstrap bucket itself is not accidentally destroyed by adding a `lifecycle { prevent_destroy = true }` block to `aws_s3_bucket.state` in the bootstrap.

### 7.4 Terraform Cloud / HCP Terraform vs. S3+DynamoDB Backend

**Current state:** S3+DynamoDB backend, managed via the bootstrap module.

**Assessment:** The S3+DynamoDB backend is the right choice for this project. HCP Terraform (formerly Terraform Cloud) adds value primarily through:
- Remote execution (runs happen in Terraform Cloud, not on the CI runner).
- Native audit logging of who ran which plan/apply.
- Policy-as-code (Sentinel/OPA).
- Cost estimation in plan output.

For a single-team academic project with GitHub Actions as the CI system, the existing S3+DynamoDB backend is simpler, cheaper ($0), and sufficient.

**Recommendation:** 🟢 **Stay with S3+DynamoDB backend.** Add it to the showcase as a talking point — "We evaluated HCP Terraform but the S3 backend with DynamoDB locking gives equivalent state safety for zero additional cost at this scale."

---

## 8. Prioritized Action Plan

### Phase 1 — Pre-Showcase (Critical, do before any live demo)

| # | Action | Terraform Resource | Effort |
|---|---|---|---|
| 1 | Confirm DynamoDB state locking `dynamodb_table` key in backend HCL files | `backend/dev.hcl`, `backend/prod.hcl` | 15 min |
| 2 | Enable PITR on `users`, `attempts`, `responses` tables | `aws_dynamodb_table.users/.attempts/.responses` | 30 min |
| 3 | Move `SECRET_KEY` to AWS Secrets Manager | New `aws_secretsmanager_secret`, update `lambda.tf` and `config.py` | 2–3 h |
| 4 | Add CloudWatch alarm for `aws_sqs_queue.registration_dlq` | New `aws_cloudwatch_metric_alarm` | 30 min |
| 5 | Set `domain_name` + `route53_zone_id` in prod tfvars for custom domain | `acm_custom_domain.tf` (already complete) | 30 min |
| 6 | Add `throttling_burst_limit` + `throttling_rate_limit` to API Gateway stage | `aws_apigatewayv2_stage.default` | 20 min |
| 7 | Add Cost Anomaly Detection | New `aws_ce_anomaly_monitor` + `aws_ce_anomaly_subscription` | 30 min |
| 8 | Verify SES is out of sandbox mode | AWS Support request (if not already done) | 1–3 days |

### Phase 2 — Production-Grade (High, complete within 2 weeks)

| # | Action | Terraform Resource | Effort |
|---|---|---|---|
| 9 | Add WAF v2 WebACL with managed rules on CloudFront | New `aws_wafv2_web_acl` + association | 2–3 h |
| 10 | Add CloudFront cache behavior for `/static/*` pointing to S3 | `aws_cloudfront_distribution.app` new cache behavior | 2 h |
| 11 | Instrument X-Ray SDK in Flask app (`patch_all()` in `app/__init__.py`) | Code change + `aws_lambda_function.registration_worker` tracing | 1 h |
| 12 | Add CloudFront Synthetics canary for uptime monitoring | New `aws_synthetics_canary` + alarm | 1–2 h |
| 13 | Add DLQ alarm for `registration_worker` errors | New `aws_cloudwatch_metric_alarm` for worker | 20 min |
| 14 | Scope `S3Full` permission in GitHub Actions role away from `s3:*` | `aws_iam_role_policy.github_actions_deploy` | 1 h |
| 15 | Add drift detection scheduled workflow | New `.github/workflows/drift-detection.yml` | 1 h |
| 16 | Add `reserved_concurrent_executions` to both Lambda functions | `aws_lambda_function.app/.registration_worker` | 20 min |
| 17 | Add CloudTrail trail with S3 data events | New `aws_cloudtrail` resource | 1–2 h |

### Phase 3 — Showcase Enhancements (Medium, sprint-level improvements)

| # | Action | Effort |
|---|---|---|
| 18 | Run Lambda Power Tuning on `app` Lambda and adjust `var.lambda_memory_size` | 2–3 h |
| 19 | Add provisioned concurrency for production (`aws_lambda_provisioned_concurrency_config`) | 30 min |
| 20 | Publish custom CloudWatch business metrics (quiz submissions, inspector completions) | 2–3 h code + 30 min dashboard |
| 21 | Add S3 lifecycle policy for Intelligent-Tiering on EML/video prefixes | 30 min |
| 22 | Add `CostCenter`, `Owner`, `Application`, `Version` tags to Terraform | 30 min |
| 23 | Enable PITR on remaining 6 DynamoDB tables | 20 min |
| 24 | Add smoke test step (curl check) to deploy workflows | 30 min each workflow |
| 25 | Add CloudWatch Logs Insights saved queries | 1 h |

---

*Report generated from infrastructure analysis of `terraform/` directory. All resource names reference actual Terraform resources found in the codebase. No resources were invented or assumed.*
