# CLAUDE.md - Project Context for Claude Code

## Project Overview
**Phishing Awareness Training Application** (Flask + AWS Serverless + Terraform).
This is a SecDevOps project for ESME engineering school, featuring interactive quizzes and a real-world "Email Threat Inspector".

## Key Resources
- **Documentation**: See `documentation/README.md` for full Dev, Operator, and User guides.
- **Skills**: Specialized Gemini CLI skills are available for this project:
    - `phishing-content-creator`: Generates new .eml samples.
    - `cloud-secdevops-auditor`: Checks IAM/S3 security.
    - `aws-lambda-ops-shorthand`: Quick logs/sync commands.

## Architecture
- **Backend**: Flask (Python 3.12) adapted for Lambda via `mangum`.
- **Database**: AWS DynamoDB (Boto3 models in `app/models.py`).
- **Infrastructure**: Terraform (`terraform/` directory).
- **CI/CD**: GitLab CI (`.gitlab-ci.yml`).

## Recent Features (2026-02-20)
- **Bug Reporting**: Global "Report Bug" modal + Admin management view (`/dashboard/bugs`).
- **Inspector Troubleshooting**: Admin view (`/inspector/answer-key`) to preview email parsing and verify ground truths.
- **Privacy**: Automated placeholder cleaning for .eml files (e.g., `{{.FirstName}}` -> "Valued Customer").
- **GDPR**: Anonymous inspector attempts table (`DYNAMODB_INSPECTOR_ANON`).

## Common Tasks
- **Run Local**: `python run.py` (Port 5000).
- **Test**: `make test` (Uses `pytest` + `moto`).
- **Lint**: `make lint` (Uses `flake8`).
- **Deploy**: managed via GitLab CI, but local `terraform apply` works for dev.

## Code Conventions
- **Blueprints**: `app/auth`, `app/quiz`, `app/inspector`, `app/dashboard`.
- **Models**: ALL DynamoDB access must go through `app/models.py`.
- **Secrets**: Never commit. Use `config.py` + Environment Variables.
