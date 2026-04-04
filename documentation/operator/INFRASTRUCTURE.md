# Infrastructure as Code — Phishing Awareness Training

![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?logo=awslambda&logoColor=white)
![DynamoDB](https://img.shields.io/badge/DynamoDB-4053D6?logo=amazondynamodb&logoColor=white)
![Amazon S3](https://img.shields.io/badge/Amazon_S3-569A31?logo=amazons3&logoColor=white)
![Amazon SQS](https://img.shields.io/badge/Amazon_SQS-FF4F8B?logo=amazonsqs&logoColor=white)
![CloudFront](https://img.shields.io/badge/CloudFront-232F3E?logo=amazonaws&logoColor=white)
![CloudWatch](https://img.shields.io/badge/CloudWatch-FF4F8B?logo=amazonaws&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?logo=terraform&logoColor=white)

## Infrastructure Overview

The application uses a serverless AWS architecture managed entirely via **Terraform** (`phishing-platform-infra/terraform/` directory).

```mermaid
architecture-beta
    group awscloud(cloud)[AWS Cloud] {
        service client(internet)[Client Browser]
        service api_gateway(logos:aws-api-gateway)[API Gateway] in awscloud
        service lambda_function(logos:aws-lambda)[Lambda Function] in awscloud
        service dynamodb_table(logos:aws-dynamodb)[DynamoDB Tables] in awscloud
        service s3_bucket(logos:aws-s3)[S3 Bucket] in awscloud
        service cloudwatch(logos:aws-cloudwatch)[CloudWatch Logs] in awscloud

        client:R -- "HTTP(S)" --> L:api_gateway
        api_gateway:R -- "Triggers" --> L:lambda_function
        lambda_function:R -- "Read/Write" --> L:dynamodb_table
        lambda_function:B -- "Fetch EML" --> T:s3_bucket
        lambda_function:L -- "Log Events" --> R:cloudwatch
    }
```

---

## AWS Resource Mapping

Infrastructure is located in the `phishing-platform-infra/terraform/` directory.

### Bootstrap (Initial Setup)

Before deploying the main infrastructure, a bootstrap process (`phishing-platform-infra/terraform/bootstrap/`) creates:
- **S3 Bucket** (`phishing-terraform-state`): Terraform remote state storage.
- **DynamoDB Table** (`phishing-terraform-locks`): Terraform state locking (`LockID`).

### Computing (Serverless)

Two Lambda functions are deployed:

**Main Flask App (`phishing-app-{env}-app`)**
- Runtime: `python3.12` · Memory: 512 MB · Timeout: 30 s · X-Ray active tracing
- Environment variables set by Terraform: `SECRET_KEY`, `AWS_REGION_NAME`, all `DYNAMODB_*` table names, `S3_BUCKET`, `SQS_REGISTRATION_QUEUE_URL`, `SES_FROM_EMAIL`, `VIDEO_BASE_URL`

**Registration Worker (`phishing-app-{env}-registration-worker`)**
- Runtime: `python3.12` · Memory: 256 MB · Timeout: 60 s
- Triggered by SQS registration queue (batch size: 1)
- Creates user in DynamoDB, sends SES confirmation email, publishes SNS event

**API Gateway (v2 HTTP API)**
- AWS Lambda Proxy integration · `$default` stage · auto-deploy
- Structured JSON access logs → CloudWatch

### NoSQL Database (DynamoDB — 9 tables, PAY_PER_REQUEST)

All tables use on-demand billing. The `{prefix}` is `phishing-app-{env}`.

| Table | PK | SK | GSIs | Notes |
|---|---|---|---|---|
| `{prefix}-users` | `username` | — | `email-index`, `group-index` | Cohort fields + inspector state |
| `{prefix}-quizzes` | `quiz_id` | — | — | Quiz definitions with embedded questions |
| `{prefix}-attempts` | `username` | `quiz_id` | `quiz-index`, `group-index` | One per user per quiz |
| `{prefix}-responses` | `username_quiz_id` | `question_id` | `quiz-question-index` | Per-question answers |
| `{prefix}-inspector-attempts` | `username` | `submitted_at` | `group-index`, `email-index` | Authenticated attempts (legacy) |
| `{prefix}-inspector-attempts-anon` | `attempt_id` | `submitted_at` | — | GDPR-safe anonymous attempts |
| `{prefix}-bugs` | `bug_id` | — | — | User-submitted bug reports |
| `{prefix}-answer-key-overrides` | `email_file` | — | — | Admin-editable answer key overrides |
| `{prefix}-cohort-tokens` | `token` | — | — | QR registration tokens · TTL: 90 days |

### Storage (S3)

**Bucket**: `phishing-app-{env}-eu-west-3`
- Versioning enabled · AES256 server-side encryption
- `videos/*` — public read in `dev` environment for training video access
- `eml-samples/` — private; EML files loaded by the inspector
- `reports/` — private; generated CSV reports with 1-hour pre-signed download URLs

### Async Messaging (SQS + SES + SNS)

**SQS Registration Queue** (`phishing-app-{env}-registration`)
- Standard queue · SSE · 60 s visibility timeout · 1-day retention
- Flask app sends registration payloads here; the Lambda worker consumes them

**SQS Dead-Letter Queue** (`phishing-app-{env}-registration-dlq`)
- 14-day retention · `maxReceiveCount=4`
- Catches messages that fail processing after 4 attempts

**SES Email Identity** — sends `no-reply@...` confirmation emails to newly registered students

**SNS Topics**:
- `phishing-app-{env}-registration` — registration event fan-out (future extensions)
- `phishing-app-{env}-alerts` — CloudWatch alarm delivery; optional email subscription

### Monitoring (CloudWatch)

- **Log Groups**: `/aws/lambda/phishing-app-{env}-app`, `/aws/lambda/phishing-app-{env}-registration-worker`, `/aws/apigateway/phishing-app-{env}-api` — 14-day retention
- **Dashboard**: `phishing-app-{env}-overview` — 3 rows: Lambda · API GW · DynamoDB
- **Alarms (6)**: Lambda errors/duration-p95/throttles · API GW 4xx/5xx · DynamoDB system errors

### CDN (CloudFront)

Distribution in front of API Gateway:
- TTL = 0 (all requests forwarded — correct for session-based app)
- All cookies and query strings forwarded; all 7 HTTP methods allowed
- HTTP → HTTPS redirect enforced
- Provides a stable URL that survives API Gateway destroy-recreate cycles

---

## Configuration Variables

Managed in `phishing-platform-infra/terraform/variables.tf` and `phishing-platform-infra/terraform/env/*.tfvars`.

| Variable | Description | Default |
|---|---|---|
| `aws_region` | AWS region for all resources | `eu-west-3` |
| `environment` | Deployment environment (`dev`, `prod`) | `prod` |
| `app_name` | Prefix for all resources | `phishing-app` |
| `lambda_memory_size` | Flask app Lambda memory in MB | `512` |
| `lambda_timeout` | Flask app Lambda timeout in seconds | `30` |
| `secret_key` | Flask `SECRET_KEY` (sensitive) | — |
| `ses_from_email` | Confirmation email sender address | — |
| `alert_email` | Optional SNS email for CloudWatch alarms | — |

---

## Security & IAM

- **Lambda Execution Role** (`phishing-app-{env}-lambda-role`): DynamoDB (9 tables + GSIs), S3, SQS `SendMessage`, X-Ray
- **Registration Worker Role** (`phishing-app-{env}-registration-worker-role`): DynamoDB users table, SES `SendEmail`, SQS `Receive+Delete`, SNS `Publish`
- **GitHub Actions OIDC Role** (`phishing-app-{env}-github-actions-deploy`): Full deploy permissions scoped to this repo via OIDC — no static credentials
- All resources are prefixed with `${var.app_name}-${var.environment}` for clear ownership
