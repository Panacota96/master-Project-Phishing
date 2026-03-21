# En Garde — Requirements

## Infrastructure Requirements

| Resource | Purpose | Notes |
|---|---|---|
| AWS Lambda `en-garde-{env}-app` (Python 3.12, 512 MB, 30 s) | App runtime | Via mangum + asgiref |
| AWS Lambda `en-garde-{env}-registration-worker` (Python 3.12, 256 MB, 60 s) | Async user registration + SES email | Triggered by SQS |
| API Gateway v2 (HTTP API) | Public HTTPS entry | `$default` stage, auto-deploy, structured JSON access logs |
| CloudFront Distribution | CDN + HTTPS termination, stable URL | TTL=0 (all requests forwarded), redirect-to-https; custom domain + ACM optional |
| S3 Bucket (`en-garde-{env}-{region}`) | EML samples, video assets, generated reports | AES256 encryption, versioning enabled; `videos/*` public-read in dev |
| DynamoDB (9 tables, PAY_PER_REQUEST) | All app data | On-demand billing, see schema below |
| Route 53 + ACM | Custom domain (optional) | ACM cert provisioned in us-east-1 for CloudFront |
| CloudWatch Log Groups (3) | Lambda app, Lambda worker, API GW logs | 14-day retention |
| CloudWatch Alarms (6) | Lambda/API GW/DynamoDB monitoring | SNS email alerts; see alarm list below |
| CloudWatch Dashboard | Ops overview — 3 rows: Lambda, API GW, DynamoDB | `en-garde-{env}-overview` |
| SNS Topic `en-garde-{env}-alerts` | CloudWatch alarm delivery | Email subscription (optional, via `alert_email` variable) |
| SNS Topic `en-garde-{env}-registration` | Registration event fan-out | Available for future extensions |
| SQS Queue `en-garde-{env}-registration` | Async user registration queue | Standard queue, SSE, 60 s visibility, 1-day retention |
| SQS DLQ `en-garde-{env}-registration-dlq` | Dead-letter queue for failed registrations | 14-day retention, maxReceiveCount=4 |
| SES Email Identity | Confirmation emails to new students | `no-reply@engarde.esme.fr`; set `ses_from_email` var |
| Terraform State S3 + DynamoDB | IaC state management | `phishing-terraform-state` bucket + `phishing-terraform-locks` table |
| GitHub Actions OIDC Provider | Keyless CI/CD authentication | `token.actions.githubusercontent.com` |

### DynamoDB Tables (9)

| Table name pattern | PK | SK | GSIs |
|---|---|---|---|
| `{prefix}-users` | `username` | — | `email-index` (email), `group-index` (group+username) |
| `{prefix}-quizzes` | `quiz_id` | — | — |
| `{prefix}-attempts` | `username` | `quiz_id` | `quiz-index` (quiz_id+completed_at), `group-index` (group+completed_at) |
| `{prefix}-responses` | `username_quiz_id` | `question_id` | `quiz-question-index` (quiz_question_id+username) |
| `{prefix}-inspector-attempts` | `username` | `submitted_at` | `group-index` (group+submitted_at), `email-index` (email_file+submitted_at) |
| `{prefix}-inspector-attempts-anon` | `attempt_id` | `submitted_at` | — |
| `{prefix}-bugs` | `bug_id` | — | — |
| `{prefix}-answer-key-overrides` | `email_file` | — | — |
| `{prefix}-cohort-tokens` | `token` | — | TTL on `expires_at` (90 days) |

### CloudWatch Alarms (6)

| Alarm name | Metric | Threshold |
|---|---|---|
| `{prefix}-lambda-errors` | Lambda Errors (Sum, 5 min) | >= 5 |
| `{prefix}-lambda-duration-p95` | Lambda Duration (p95, 5 min) | >= 25 000 ms |
| `{prefix}-lambda-throttles` | Lambda Throttles (Sum, 5 min) | >= 1 |
| `{prefix}-apigw-5xx` | API Gateway 5XXError (Sum, 5 min) | >= 3 |
| `{prefix}-apigw-4xx` | API Gateway 4XXError (Sum, 5 min) | >= 50 |
| `{prefix}-dynamodb-system-errors` | DynamoDB SystemErrors (Sum, 5 min) | >= 1 |

---

## Functional Requirements

### Authentication

| ID | Requirement |
|---|---|
| AUTH-01 | Users authenticate with username + password (Werkzeug `generate_password_hash`/`check_password_hash`) |
| AUTH-02 | Admins (`is_admin=True`) access the full dashboard; students see only quiz + inspector |
| AUTH-03 | Admins can bulk-import students via CSV upload (`/auth/admin/import-users`); required columns: `username`, `email`, `password`, `class`, `academic_year`, `major`, `facility`; optional: `group` |
| AUTH-04 | Admins can create individual student accounts via the Users admin page |
| AUTH-05 | Admins can generate a QR code that links to the self-registration page (`/auth/register`) |
| AUTH-06 | Self-registration enqueues the registration payload to SQS; the Lambda worker creates the DynamoDB user record and sends a confirmation email via SES |
| AUTH-07 | Students can change their own password; session is invalidated on change |
| AUTH-08 | No public registration link is shown in the navbar; the registration page is only reached via QR code or direct URL |

### Quiz

| ID | Requirement |
|---|---|
| QUIZ-01 | Students see a list of all available quizzes with their completion status |
| QUIZ-02 | Each quiz that has a `video_url` requires watching the training video before starting (enforced via `session['quiz_video_watched']`) |
| QUIZ-03 | Exactly one attempt per student per quiz (enforced by a DynamoDB `attribute_not_exists` condition expression) |
| QUIZ-04 | After each question answer, the student sees an explanation before continuing |
| QUIZ-05 | At quiz completion, a results page shows score, percentage, and a rank badge (Novice / Trainee / Defender / Cyber Sentinel) |
| QUIZ-06 | Quiz history page shows all past attempts, average score, completion percentage, and rank |

### Email Threat Inspector

| ID | Requirement |
|---|---|
| INSP-01 | The inspector builds a per-session pool of up to 8 emails: 1–3 spam + phishing to fill the rest, sampled from EML files present both in S3 (`eml-samples/`) and in the effective answer key |
| INSP-02 | Each email can be retrieved individually for full analysis: headers, sandboxed HTML preview, extracted links, attachment list, and auto-detected security warnings |
| INSP-03 | Students classify each email as Spam or Phishing; Phishing requires selecting exactly N signals (N = `len(answer_key[file].signals)`) |
| INSP-04 | Signal names are normalized (lowercase, alphanumeric only) on both client and server before comparison |
| INSP-05 | Submissions are stored in the anonymous table (`inspector-attempts-anon`); no username is stored for GDPR compliance |
| INSP-06 | After submitting all 8 emails, the inspector is locked for that student until an admin resets it |
| INSP-07 | Admins are never locked and can resubmit any email for testing |
| INSP-08 | Admins can reset inspector state for individual users or in bulk (by cohort filter or all users) |
| INSP-09 | The static `ANSWER_KEY` in `answer_key.py` can be overridden per email at runtime via the DynamoDB `answer-key-overrides` table; overrides take precedence via `get_effective_answer_key()` |
| INSP-10 | Admins can edit and reset answer key overrides from the admin dashboard without a code deployment |
| INSP-11 | Template placeholders (GoPhish / bracket / Jinja styles) are cleaned from EML content before display |

### Admin Dashboard

| ID | Requirement |
|---|---|
| DASH-01 | Dashboard main page shows: total users, total quiz attempts, average score, score distribution chart, per-quiz stats, cohort stats, inspector summary, signal accuracy chart, per-email accuracy |
| DASH-02 | Live stats endpoint (`GET /dashboard/api/stats`) polled by the dashboard every 30 seconds |
| DASH-03 | Real-time threat feed widget fetches and defangs the top 10 URLs from OpenPhish (1-hour in-memory cache) |
| DASH-04 | Risk Dashboard (`/dashboard/risk`) calculates a 0–100 risk score per cohort based on signal miss rate and quiz failure rate |
| DASH-05 | Quiz CSV reports (summary or detailed per-cohort/quiz) can be generated, uploaded to S3, and downloaded via a 1-hour pre-signed URL |
| DASH-06 | Inspector CSV reports (by cohort or by email) with the same filter and date-range options as the analytics page |
| DASH-07 | Bug reports submitted by students are visible to admins in the Bugs list |

### Email Registration Worker

| ID | Requirement |
|---|---|
| WORK-01 | The Lambda worker is triggered by the SQS registration queue with `batch_size=1` |
| WORK-02 | The worker performs idempotency checks: duplicate username and duplicate email queries before writing |
| WORK-03 | The worker writes the user record to DynamoDB with `attribute_not_exists(username)` condition |
| WORK-04 | After a successful write, the worker sends a confirmation email via SES with the login URL |
| WORK-05 | After a successful write, the worker publishes an event to the SNS registration topic |
| WORK-06 | Failed messages (after 4 receive attempts) are moved to the DLQ with 14-day retention |

---

## Cloud Requirements

- AWS account with admin access for bootstrap (temporary); OIDC role used for ongoing CI.
- Primary region: **eu-west-3** (Paris). ACM certificate for custom domain must be provisioned in **us-east-1**.
- GitHub repository: `Panacota96/master-Project-Phishing`
- GitHub Actions environment named **`dev`** with the following secrets/variables:

| Type | Name | Description |
|---|---|---|
| Secret | `AWS_DEPLOY_ROLE_ARN` | IAM role ARN output from `terraform output github_actions_deploy_role_arn` |
| Secret | `TF_VAR_SECRET_KEY` | Flask secret key (`python3 -c "import secrets; print(secrets.token_hex(32))"`) |
| Variable | `TF_VAR_ROUTE53_ZONE_ID` | Route 53 hosted zone ID (optional — skip for no custom domain) |

For production deployments, a separate **`prod`** GitHub environment is required with the same secrets.

---

## Software Requirements

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12 | App runtime + local dev |
| Terraform | >= 1.5 (tested with ~1.9) | Infrastructure provisioning |
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
| requests | 2.32.3 | HTTP client (OpenPhish threat feed) |
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
- **DynamoDB**: `PutItem`, `GetItem`, `Query` on the users table and its GSIs
- **SES**: `SendEmail`
- **SQS**: `ReceiveMessage`, `DeleteMessage`, `GetQueueAttributes` on the registration queue
- **SNS**: `Publish` on the registration topic

### GitHub Actions OIDC Deploy Role — `en-garde-{env}-github-actions-deploy`

| Sid | Actions | Resource scope |
|---|---|---|
| `LambdaCRUD` | CreateFunction, DeleteFunction, GetFunction, GetFunctionConfiguration, UpdateFunctionCode, UpdateFunctionConfiguration, AddPermission, RemovePermission, GetPolicy, ListVersionsByFunction, PublishVersion, CreateEventSourceMapping, DeleteEventSourceMapping, GetEventSourceMapping, UpdateEventSourceMapping, ListEventSourceMappings, GetFunctionCodeSigningConfig, TagResource, UntagResource, ListTags | `*` |
| `IAMRoleManagement` | CreateRole, DeleteRole, GetRole, TagRole, PassRole, ListInstanceProfilesForRole, Attach/DetachRolePolicy, Put/Delete/GetRolePolicy, ListRolePolicies, ListAttachedRolePolicies, OIDC provider management (Create/Delete/Get/Update/Tag) | `*` |
| `DynamoDB` | CreateTable, DescribeTable, DeleteTable, UpdateTable, CRUD operations, DescribeTimeToLive, UpdateTimeToLive, ListTagsOfResource, TagResource, DescribeContinuousBackups | `arn:aws:dynamodb:*:*:table/en-garde-*`, `phishing-terraform-locks` |
| `S3Full` | `s3:*` | `en-garde-dev-*` and `phishing-terraform-state` buckets |
| `APIGateway` | `apigateway:*` | `*` |
| `CloudFront` | CreateDistribution, DeleteDistribution, Get/Update/ListDistributions, TagResource, UntagResource, ListTagsForResource | `*` |
| `CloudWatchLogs` | CreateLogGroup, DeleteLogGroup, PutRetentionPolicy, TagLogGroup, ListTagsLogGroup, ListLogDeliveries | `arn:aws:logs:*:*:log-group:/aws/*` |
| `CloudWatchLogsDescribe` | DescribeLogGroups, ListTagsForResource | `*` |
| `CloudWatchAlarmsDashboards` | PutMetricAlarm, DeleteAlarms, DescribeAlarms, ListTagsForResource, PutDashboard, DeleteDashboards, GetDashboard | `*` |
| `SNS` | CreateTopic, DeleteTopic, Subscribe, Unsubscribe, GetTopicAttributes, SetTopicAttributes, ListTagsForResource, TagResource, GetSubscriptionAttributes, ListSubscriptionsByTopic | `*` |
| `SQS` | CreateQueue, DeleteQueue, GetQueueAttributes, SetQueueAttributes, TagQueue, GetQueueUrl, ListQueueTags | `*` |
| `SES` | VerifyEmailIdentity, VerifyDomainIdentity, GetIdentityVerificationAttributes, DeleteIdentity, SetIdentityNotificationTopic, GetSendQuota, ListIdentities | `*` |
| `ACMAndRoute53` | ACM: RequestCertificate, DescribeCertificate, DeleteCertificate, ListCertificates, AddTagsToCertificate; Route 53: ChangeResourceRecordSets, GetChange, ListHostedZones, ListResourceRecordSets | `*` |
| `XRay` | CreateGroup, DeleteGroup, GetGroup, UpdateGroup | `*` |

---

## Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Serverless | App runs on AWS Lambda (no persistent server); scales to zero when idle |
| NFR-02 | IaC | All AWS resources managed by Terraform; state stored remotely in S3 + DynamoDB lock |
| NFR-03 | CI/CD | Every push to `main` triggers lint + EML validation + tests + Lambda build + Terraform plan/apply (dev); prod deploy is manual via `workflow_dispatch` |
| NFR-04 | Security | GitHub Actions uses OIDC (no static AWS keys); S3 versioning + AES256 at rest; CSRF protection on all forms; `WTF_CSRF_SSL_STRICT=False` for CloudFront Referer header |
| NFR-05 | Observability | AWS X-Ray active tracing on the Flask Lambda; CloudWatch structured JSON logs for API GW; 6 metric alarms → SNS → email; CloudWatch dashboard with Lambda + API GW + DynamoDB metrics |
| NFR-06 | GDPR | Inspector submissions stored without username in the `inspector-attempts-anon` table; authenticated table (`inspector-attempts`) retained for analytics with cohort fields only |
| NFR-07 | Availability | CloudFront provides a stable URL that survives API Gateway/Lambda destroy-recreate cycles |
| NFR-08 | Portability | Docker Compose setup (DynamoDB Local + Gunicorn + Nginx) for fully offline local development |

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
