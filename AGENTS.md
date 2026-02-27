# Repository Guidelines

## Project Structure & Module Organization
- `app/`: Flask app factory, blueprints (`auth/`, `quiz/`, `dashboard/`, `inspector/`), templates, and static assets.
- `tests/`: Pytest suite (`test_auth.py`, `test_models.py`, `test_quiz.py`) plus fixtures in `conftest.py`.
- `examples/`: Real `.eml` samples used by the inspector.
- `aws/`, `terraform/`, `nginx/`: Deployment and infrastructure assets.
- `terraform/bootstrap/`: Terraform state bucket + lock table bootstrap.
- `terraform/bootstrap/README.md`: Bootstrap instructions for remote state.
- `terraform/backend/`: Backend configs for dev/prod state.
- `terraform/env/`: Example tfvars for dev/prod.
- Root scripts: `run.py` (dev entrypoint), `seed_dynamodb.py` (DynamoDB seed), `lambda_handler.py` (AWS Lambda).

## Build, Test, and Development Commands
- `pip install -r requirements.txt`: install Python dependencies.
- `python seed_dynamodb.py`: seed DynamoDB data (admin + quiz).
- `python run.py`: run the Flask dev server at `http://localhost:5000`.
- `docker compose up -d --build`: run Nginx + Gunicorn + Flask locally.
- `pytest tests/ -v`: run automated tests.
- `./scripts/build_lambda.sh`: build the `lambda.zip` deployment artifact.
- `make lambda`: standard target for building `lambda.zip`.
- `make test`: run automated tests via pytest.
- `make lint`: run flake8 with repo settings.
- `./scripts/backfill_cohorts.py --apply`: backfill cohort fields (class/year/major) for GDPR group-only analytics.
- `./scripts/backfill_cohorts.py --mapping-csv path/to/cohorts.csv --apply`: override cohorts from a CSV mapping.

## Deployment Documentation (Screenshot Checklist)
- Bootstrap (AWS console):
  - S3 state bucket details page (versioning enabled).
  - DynamoDB lock table details page.
- Terraform init (terminal):
  - `terraform init -backend-config=backend/dev.hcl` success output.
- Terraform plan (terminal):
  - `terraform plan -var-file=env/dev.tfvars` summary (add/change/destroy counts).
- Terraform apply (terminal):
  - `terraform apply -var-file=env/dev.tfvars` success output.
  - Terraform outputs showing API Gateway URL.
- S3 upload (console):
  - `eml-samples/` prefix listing with `.eml` files.
- Seed data (terminal):
  - `seed_dynamodb.py` output showing admin + quiz created.
- App verification (browser):
  - Login page at API Gateway URL.
  - Successful login (flash message) and quiz list page.

## Reproducibility Notes
- Always use a virtual environment for Python (`python3 -m venv .venv`).
- Use `AWS_PROFILE` to switch accounts safely.
- Replace `<env>` placeholders with your target environment (e.g., `dev`, `prod`).

## Session Notes (2026-02-27)
- Editable answer key implemented: admins can override any email's classification and signals via the UI without a code deploy.
- `DYNAMODB_ANSWER_KEY_OVERRIDES` table added to all environments (Terraform, conftest, CLAUDE.md, env vars).
- `get_effective_answer_key()` in `app/models.py` merges static `answer_key.py` with DynamoDB overrides at runtime.
- Dynamic signal count: `requiredSignals` returned by `api_email_detail`; student JS and server validation both read it (no more hardcoded 3).
- New admin routes: `POST /dashboard/inspector/answer-key/edit` and `POST /dashboard/inspector/answer-key/reset`.
- All 53 tests pass.
- CloudFront distribution added (`terraform/cloudfront.tf`): stable `dXXXXX.cloudfront.net` URL that survives API Gateway destroy/recreate cycles; no custom domain or ACM certificate required.
- `terraform/outputs.tf` now exports `cloudfront_url` — run `terraform output cloudfront_url` after apply to get the URL to share with students.

## Session Notes (2026-02-18)
- Dev environment deployed via Terraform (Lambda + API Gateway + DynamoDB + S3).
- Remote state bootstrapped: S3 state bucket + DynamoDB lock table.
- CI/CD fixes applied (make in CI, JUnit report, CI secret key requirement).
- CI/CD auto-deploys dev and keeps prod manual; seeding runs every deploy (skippable via `SKIP_SEED`).
- Added `scripts/import_resources.sh` to import existing AWS resources into state.
- Added dev→prod migration scripts: `scripts/migrate_dynamodb.py` + `scripts/migrate_s3.sh` (supports `MIGRATE_DRY_RUN`).
- Added manual CI jobs: `migrate_prod`, `destroy_dev`, `destroy_prod` (optional `CLEAN_S3=true`).
- GDPR updates: group-only analytics by class/year/major; no individual reports.
- Inspector analytics now cohort-based with CSV export.
- Lambda handler uses ASGI wrapper (`asgiref` + `mangum`).

## Coding Style & Naming Conventions
- Python: 4-space indentation, PEP 8 style, `snake_case` for functions/vars, `PascalCase` for classes.
- Flask blueprints follow `app/<area>/routes.py` and `app/<area>/forms.py` naming.
- Templates live under `app/templates/<area>/` with descriptive names (e.g., `quiz_list.html`).
- Linting uses `flake8` via `make lint`; keep diffs clean and consistent.

## Testing Guidelines
- Framework: `pytest`. DynamoDB interactions are mocked with `moto` in tests.
- Test names use `test_<behavior>` methods inside `Test<Area>` classes.
- Run full suite with `pytest tests/ -v`. See `TESTING_GUIDE.md` for local DynamoDB setups.

## Commit & Pull Request Guidelines
- Commit messages follow Conventional Commits (e.g., `feat: ...`, `docs: ...`). Keep subject lines short and imperative.
- PRs should include:
  - A short summary of changes and rationale.
  - Test results (`pytest tests/ -v` or note if not run).
  - Screenshots for UI changes (templates/CSS).
  - Links to related issues or tasks when applicable.

## Security & Configuration Tips
- Default admin credentials are `admin` / `admin123` (change for real deployments).
- Configure secrets and AWS resources via env vars (see `aws/env.example`).
- Do not commit real AWS keys or production secrets.
- CI/CD requires `TF_VAR_secret_key` set in GitLab variables.
