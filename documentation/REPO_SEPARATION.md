# Repository Separation Guide

This document describes the strategy for splitting the **EnGarde** monorepo into two focused repositories: the Flask application and the AWS infrastructure.

---

## Why Split?

| Concern | Benefit of Separation |
|---|---|
| **Independent release cadence** | Deploy new app features without re-running Terraform |
| **Access control** | Limit infra credentials to the ops team; devs only need the app repo |
| **CI speed** | App CI runs only linting/tests/Lambda build (no Terraform plan) |
| **Clear ownership** | Developers own the app repo; cloud engineers own the infra repo |

---

## Current Monorepo Layout

The project is currently a single repository with a clean logical split already in place:

```
master-Project-Phishing/          ← App repo candidate
├── app/                          # Flask blueprints + models
├── tests/                        # Pytest suite
├── scripts/                      # Build & utility scripts
├── examples/                     # .eml sample library
├── nginx/                        # Nginx config
├── documentation/                # Full documentation suite
├── data/                         # Static seed data
├── config.py                     # App configuration
├── run.py                        # Dev entry point
├── lambda_handler.py             # Lambda entry point (Mangum)
├── seed_dynamodb.py              # DynamoDB seeding
├── setup_local_db.py             # Local table creation
├── requirements.txt              # Python dependencies
├── Dockerfile                    # App container
├── docker-compose.yml            # Local dev stack
└── Makefile                      # Build shortcuts

phishing-platform-infra/          ← Infra repo candidate
├── terraform/                    # All Terraform IaC (Lambda, DDB, S3, etc.)
├── lambda/                       # Lambda function source code
│   ├── campaign_mailer/          # Campaign mailer Lambda (SQS → SES)
│   └── registration_worker/      # Registration worker Lambda (SQS → DDB → SES)
├── ansible/                      # Optional Ansible VM playbooks
├── aws/                          # Legacy EC2 helpers (deprecated)
└── scripts/                      # Migration and resource-import helpers
```

---

## Step-by-Step Split Procedure

### Step 1 — Create the Infra Repository

```bash
# Clone the monorepo and extract the infra subtree
git clone https://github.com/Panacota96/master-Project-Phishing engarde-infra
cd engarde-infra

# Keep only the infra directory history (requires git-filter-repo)
git filter-repo --subdirectory-filter phishing-platform-infra --force

# Push to a new remote
git remote add origin https://github.com/<org>/engarde-infra.git
git push -u origin main
```

> **Tip:** If `git filter-repo` is not available, use `git subtree split`:
> ```bash
> git subtree split --prefix=phishing-platform-infra -b infra-split
> git push origin infra-split:main
> ```

### Step 2 — Clean the App Repository

After creating the infra repo, remove the infra directory from the app repo:

```bash
# In the app repo
git filter-repo --path phishing-platform-infra --invert-paths --force
```

Or, for a simpler non-history-rewriting approach, just `git rm -r phishing-platform-infra` and add a note in the README pointing to the new infra repo.

### Step 3 — Update CI/CD

**App repository CI** (`.github/workflows/ci.yml`):
- Runs lint, test, and builds `lambda.zip`, `registration_worker.zip`, `campaign_mailer.zip`
- Publishes the zip artifacts (GitHub releases or S3)
- No Terraform needed

**Infra repository CI**:
- Downloads Lambda artifacts from the app repo's published release or S3
- Runs `terraform plan` / `terraform apply`
- Triggers on changes to `terraform/`, `lambda/`, or manual dispatch

Example artifact handoff (infra workflow step):
```yaml
- name: Download app artifacts
  run: |
    aws s3 cp s3://<artifact-bucket>/lambda.zip .
    aws s3 cp s3://<artifact-bucket>/registration_worker.zip .
    aws s3 cp s3://<artifact-bucket>/campaign_mailer.zip .
```

### Step 4 — Update Terraform `filename` References

Terraform currently expects zip files relative to the module path:
```hcl
filename = "${path.module}/../campaign_mailer.zip"
```

After the split, the infra CI would download zips to a known path before running Terraform, so you can either:
- Keep the same `../campaign_mailer.zip` convention (download into repo root)
- Use a Terraform variable: `var.campaign_mailer_zip_path`

### Step 5 — Update Documentation Cross-References

Update any links in both repositories' READMEs to point across repos where needed.

---

## Environment Variables Shared Between Repos

The Lambda functions and Terraform outputs share a set of environment variable names. Keep a single source of truth in `documentation/operator/INFRASTRUCTURE.md` (or a shared `.env.example` committed to both repos) so both teams stay in sync.

Key shared variables:

| Variable | Set by | Consumed by |
|---|---|---|
| `DYNAMODB_USERS` | Terraform output | Flask app, Lambda workers |
| `S3_BUCKET` | Terraform output | Flask app |
| `SQS_REGISTRATION_QUEUE_URL` | Terraform output | Flask app |
| `SQS_CAMPAIGN_QUEUE_URL` | Terraform output | Flask app |
| `REDIS_ENDPOINT` | Terraform output | Flask app, campaign mailer |
| `SES_FROM_EMAIL` | Manual / tfvars | Registration worker, campaign mailer |

---

## Monorepo vs Split — When to Stay Merged

If the team is small (< 5 contributors) and deployments always combine an app change with an infra change, staying in a monorepo with the current clean directory separation is perfectly valid. The `phishing-platform-infra/` boundary already provides the logical separation needed for access control via **CODEOWNERS** and branch protection rules.

To enforce this without splitting:
```
# .github/CODEOWNERS
/phishing-platform-infra/   @ops-team
/app/                        @dev-team
/tests/                      @dev-team
```
