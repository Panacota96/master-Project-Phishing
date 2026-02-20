# CODEX.md - Coding Guidelines

## Tech Stack
- **Language**: Python 3.12 (Flask)
- **Database**: AWS DynamoDB (Boto3)
- **Frontend**: Jinja2 + Bootstrap 5
- **IaC**: Terraform (AWS Provider)

## Code Structure
- **Entry Points**:
    - `run.py`: Local Flask dev server.
    - `lambda_handler.py`: AWS Lambda entry (Mangum adapter).
- **Core Logic**:
    - `app/__init__.py`: App factory pattern.
    - `app/models.py`: Centralized DynamoDB CRUD. **Do not use boto3 directly in routes.**
    - `app/inspector/routes.py`: EML parsing logic with `email` library.

## Testing & Validation
- **Framework**: Pytest with `moto` for AWS mocking.
- **Key Tests**:
    - `tests/test_inspector_parsing.py`: Iterates ALL 98 .eml examples to verify parsing and placeholder cleaning.
    - `tests/test_models.py`: Verifies DynamoDB interactions.
- **Commands**:
    - Run tests: `make test` or `pytest`.
    - Linting: `make lint` (Strict PEP 8, no trailing whitespace).

## Operational Scripts
- `scripts/build_lambda.sh`: Packages app for deployment.
- `scripts/seed_dynamodb.py`: Populates local/dev tables.
- `scripts/validate_eml_realism.py`: Checks .eml files for required headers and MIME structure.

## New Features to Maintain
- **Human Risk Dashboard**: `get_cohort_risk_analysis` in models, `/dashboard/risk` route.
- **Live Threat Ticker**: AJAX polling endpoint in dashboard routes.
- **Attachment Parsing**: Enhanced logic in `_parse_eml_detail` for malicious file detection.
- **Bug Reporting**: `create_bug_report` in models, `/report-bug` in dashboard routes.
- **Inspector Troubleshoot**: `api_email_detail` bypasses pool check for admins.
- **Placeholder Cleaning**: `_clean_placeholders` regex helper in inspector routes.

## Development Standards
- **MIME Structure**: All generated emails must be `multipart/alternative`.
- **Secrets**: No hardcoded credentials. Use environment variables.
