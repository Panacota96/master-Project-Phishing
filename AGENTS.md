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
- Root scripts: `run.py` (dev entrypoint), `seed.py` (SQLite seed), `seed_dynamodb.py` (DynamoDB seed), `lambda_handler.py` (AWS Lambda).

## Build, Test, and Development Commands
- `pip install -r requirements.txt`: install Python dependencies.
- `python seed.py`: seed local SQLite data (admin + quiz).
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
  - `terraform plan` summary (add/change/destroy counts).
- Terraform apply (terminal):
  - `terraform apply` success output.
  - Terraform outputs showing API Gateway URL.
- S3 upload (console):
  - `eml-samples/` prefix listing with `.eml` files.
- Seed data (terminal):
  - `seed_dynamodb.py` output showing admin + quiz created.
- App verification (browser):
  - Login page at API Gateway URL.
  - Successful login (flash message) and quiz list page.

## Coding Style & Naming Conventions
- Python: 4-space indentation, PEP 8 style, `snake_case` for functions/vars, `PascalCase` for classes.
- Flask blueprints follow `app/<area>/routes.py` and `app/<area>/forms.py` naming.
- Templates live under `app/templates/<area>/` with descriptive names (e.g., `quiz_list.html`).
- No formatter/linter is enforced in repo; keep diffs clean and consistent.

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
