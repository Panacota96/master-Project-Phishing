# En Garde — Requirements

## Infrastructure Requirements

| Resource | Purpose | Notes |
|---|---|---|
| AWS Lambda (Python 3.12, 512 MB) | App runtime | Via mangum |
| API Gateway v2 (HTTP API) | Public HTTPS entry | `$default` stage |
| CloudFront Distribution | CDN + HTTPS termination | Static + dynamic |
| S3 Bucket (`en-garde-{env}-{region}`) | EML samples, video assets | AES256, versioned |
| DynamoDB (9 tables) | All app data | On-demand billing |
| Route 53 + ACM | Custom domain (optional) | DNS validation cert |
| CloudWatch Log Groups (2) | Lambda + API GW logs | 14-day retention |
| CloudWatch Alarms (6) | Lambda/API GW/DynamoDB monitoring | SNS email alerts |
| CloudWatch Dashboard | Ops overview | `en-garde-{env}-overview` |
| SNS Topic (`en-garde-{env}-alerts`) | CloudWatch alarm delivery | Email subscription |
| SNS Topic (`en-garde-{env}-registration`) | Registration event fan-out | Future extensions |
| SQS Queue (`en-garde-{env}-registration`) | Async user registration queue | Standard queue, DLQ |
| SES Identity | Confirmation emails to new students | `no-reply@engarde.esme.fr` |
| Terraform State S3 + DynamoDB | IaC state management | `phishing-terraform-state` |

---

## Cloud Requirements

- AWS account with admin access for bootstrap (temporary); OIDC role used for ongoing CI.
- Primary region: **eu-west-3** (Paris). ACM certificate for custom domain must also be provisioned in **us-east-1**.
- GitHub repository: `Panacota96/master-Project-Phishing`
- GitHub Actions environment named **`dev`** with the following secrets/variables:

| Type | Name | Description |
|---|---|---|
| Secret | `AWS_DEPLOY_ROLE_ARN` | IAM role ARN output from `terraform output github_actions_deploy_role_arn` |
| Secret | `TF_VAR_SECRET_KEY` | Flask secret key (`python3 -c "import secrets; print(secrets.token_hex(32))"`) |
| Variable | `TF_VAR_ROUTE53_ZONE_ID` | Route 53 hosted zone ID (optional — skip for no custom domain) |

---

## Software Requirements

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12 | App runtime + local dev |
| Terraform | ≥ 1.5 | Infrastructure provisioning |
| AWS CLI | v2 | Asset sync, credential validation |
| Docker + Docker Compose | Latest | Local DynamoDB + Nginx |
| GitHub CLI (`gh`) | Latest | CI log inspection |
| pip deps | See `requirements.txt` | Flask, boto3, mangum, gunicorn, etc. |

### Python packages (`requirements.txt`)

| Package | Version | Purpose |
|---|---|---|
| Flask | 3.1.0 | Web framework |
| Flask-Login | 0.6.3 | Session management |
| Flask-WTF | 1.2.2 | CSRF-protected forms |
| WTForms | 3.2.1 | Form definitions + validation |
| email-validator | 2.2.0 | Email field validation |
| Werkzeug | 3.1.3 | Password hashing, WSGI utilities |
| gunicorn | 23.0.0 | WSGI server (Docker) |
| mangum | 0.19.0 | Lambda/ASGI adapter |
| boto3 | 1.35.0 | AWS SDK |
| asgiref | 3.8.1 | WSGI→ASGI bridge |
| requests | 2.32.3 | HTTP client |
| qrcode[pil] | 8.0 | QR code generation (registration flow) |
| aws-xray-sdk | 2.14.0 | Lambda-level boto3 tracing |

### Dev/test extras (not in `requirements.txt`)

| Package | Purpose |
|---|---|
| pytest | Test runner |
| moto | AWS service mocking |
| flake8 | Linting (max-line-length=120) |

---

## AWS IAM Permissions Required

### Lambda Execution Role — `en-garde-{env}-lambda-role`

- `AWSLambdaBasicExecutionRole` (managed policy) — CloudWatch Logs write
- **DynamoDB**: `GetItem`, `PutItem`, `UpdateItem`, `DeleteItem`, `Query`, `Scan`, `BatchWriteItem`, `BatchGetItem`, `ConditionCheckItem` on all 9 app tables and their GSIs
- **S3**: `GetObject`, `PutObject`, `ListBucket`, `DeleteObject` on the app bucket
- **SQS**: `SendMessage` on the registration queue (Flask app enqueues registrations)
- **X-Ray**: `PutTraceSegments`, `PutTelemetryRecords`, `GetSamplingRules`, `GetSamplingTargets`

### Registration Worker Lambda Role — `en-garde-{env}-registration-worker-role`

- `AWSLambdaBasicExecutionRole` — CloudWatch Logs write
- **DynamoDB**: `PutItem`, `GetItem` on the users table
- **SES**: `SendEmail`
- **SQS**: `ReceiveMessage`, `DeleteMessage`, `GetQueueAttributes` on the registration queue
- **SNS**: `Publish` on the registration topic

### GitHub Actions OIDC Deploy Role — `en-garde-{env}-github-actions-deploy`

| Sid | Actions | Resource scope |
|---|---|---|
| `LambdaCRUD` | CreateFunction, DeleteFunction, GetFunction, GetFunctionConfiguration, UpdateFunctionCode, UpdateFunctionConfiguration, AddPermission, RemovePermission, GetPolicy, ListVersionsByFunction, PublishVersion, CreateEventSourceMapping, DeleteEventSourceMapping, GetEventSourceMapping, UpdateEventSourceMapping, ListEventSourceMappings | `arn:aws:lambda:*:*:function:en-garde-*` |
| `IAMRoleManagement` | CreateRole, DeleteRole, GetRole, PassRole, Attach/DetachRolePolicy, Put/Delete/GetRolePolicy, ListRolePolicies, OIDC provider management | `*` |
| `DynamoDB` | CreateTable, DescribeTable, DeleteTable, UpdateTable, CRUD operations, DescribeTimeToLive, UpdateTimeToLive, ListTagsOfResource, TagResource, DescribeContinuousBackups | `arn:aws:dynamodb:*:*:table/en-garde-*`, state lock table |
| `S3Full` | `s3:*` | `en-garde-dev-*`, `phishing-terraform-state` buckets |
| `APIGateway` | `apigateway:*` | `*` |
| `CloudFront` | CreateDistribution, DeleteDistribution, Get/Update/ListDistributions, TagResource | `*` |
| `CloudWatchLogs` | CreateLogGroup, DeleteLogGroup, PutRetentionPolicy, TagLogGroup, ListTagsLogGroup, DescribeLogGroups, ListTagsForResource | Log group ARNs + `*` for Describe |
| `CloudWatchAlarms` | PutMetricAlarm, DeleteAlarms, DescribeAlarms, PutDashboard, DeleteDashboards, GetDashboard | `*` |
| `SNS` | CreateTopic, DeleteTopic, Subscribe, Unsubscribe, GetTopicAttributes, SetTopicAttributes, ListTagsForResource, TagResource | `*` |
| `SQS` | CreateQueue, DeleteQueue, GetQueueAttributes, SetQueueAttributes, TagQueue, GetQueueUrl | `*` |
| `SES` | VerifyEmailIdentity, VerifyDomainIdentity, GetIdentityVerificationAttributes, DeleteIdentity, SetIdentityNotificationTopic, GetSendQuota | `*` |
| `ACMAndRoute53` | ACM: RequestCertificate, DescribeCertificate, DeleteCertificate, ListCertificates, AddTagsToCertificate; Route 53: ChangeResourceRecordSets, GetChange, ListHostedZones, ListResourceRecordSets | `*` |
| `XRay` | CreateGroup, DeleteGroup, GetGroup, UpdateGroup | `*` |

---

## Test Requirements

- **Run**: `make test` — pytest + moto, all AWS calls mocked (no real AWS credentials needed)
- **Run**: `make lint` — flake8 with `--max-line-length=120`

### DynamoDB tables created by `conftest.py`

| Table name | Primary key | Purpose |
|---|---|---|
| `test-users` | `username` (H) | Users + GSIs on `email`, `group` |
| `test-quizzes` | `quiz_id` (H) | Quiz definitions |
| `test-attempts` | `username` (H) + `quiz_id` (R) | Quiz scores |
| `test-responses` | `username_quiz_id` (H) + `question_id` (R) | Per-question answers |
| `test-inspector` | `username` (H) + `submitted_at` (R) | Inspector attempts |
| `test-inspector-anon` | `attempt_id` (H) + `submitted_at` (R) | Anonymous inspector attempts |
| `test-answer-key-overrides` | `email_file` (H) | Answer key overrides |
| `test-bugs` | `bug_id` (H) | Bug reports |
| `test-cohort-tokens` | `token` (H) | QR registration cohort tokens |

### Key fixtures

| Fixture | Creates |
|---|---|
| `seed_admin` | `admin` / `admin123` (is_admin=True) |
| `seed_user` | `testuser` / `password123` |
| `seed_quiz` | Sample quiz with 2 questions |
| `seed_cohort_token` | Cohort token for class `engineering-2025` |

- CSRF disabled in all tests (`WTF_CSRF_ENABLED=False`)
- SQS queue created via moto for registration tests (`test-registration-queue`)

---

## Recommended Additional AWS Tools

| Tool | Why useful here |
|---|---|
| **AWS X-Ray** | End-to-end trace of Lambda → DynamoDB calls; identify slow queries; already integrated via `aws-xray-sdk` |
| **CloudWatch Logs Insights** | Ad-hoc queries on structured JSON logs; no extra infra needed; use via CloudWatch console |
| **AWS WAF** | Rate limiting + bot protection on CloudFront; prevents brute-force on `/auth/login`; add one Terraform `aws_wafv2_web_acl` resource |
| **AWS GuardDuty** | Threat detection on IAM activity, S3 access, DNS queries; enable per-account with one Terraform `aws_guardduty_detector` resource |
| **AWS Secrets Manager** | Replace `SECRET_KEY` plain Lambda env var with a managed secret and auto-rotation |
| **AWS Cost Anomaly Detection** | Alert on unexpected spend spikes; one Terraform `aws_ce_anomaly_monitor` resource, zero runtime overhead |
