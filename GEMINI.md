# GEMINI.md - Project Context: Phishing Awareness Training Application

## Project Overview
This project is a **Phishing Awareness Training Web Application** developed for the ESME engineering school Cloud SecDevOps course. It allows users to take interactive quizzes on phishing techniques and analyze real-world phishing samples using a built-in "Email Threat Inspector."

### Core Technologies
- **Backend:** Flask (Python 3.12), Flask-Login, Flask-WTF.
- **Database:** DynamoDB (AWS NoSQL) for users, quizzes, and attempts.
- **Frontend:** Jinja2 templates, Bootstrap 5, Chart.js for analytics.
- **Infrastructure:** AWS Lambda (Serverless), API Gateway, S3 (for EML storage).
- **Deployment:** Terraform (Infrastructure as Code), Docker (for local dev/production), GitLab CI/CD.

### Architecture Highlights
- **Serverless Backend:** The application is packaged using `mangum` to run on AWS Lambda.
- **Custom DynamoDB Layer:** Instead of an ORM like SQLAlchemy, `app/models.py` uses `boto3` to interact directly with DynamoDB tables.
- **Module Structure:**
    - `app/auth`: User authentication (Login, Register, Logout).
    - `app/quiz`: Quiz listing, taking quizzes, and score history.
    - `app/inspector`: EML file parser and threat analysis tool.
    - `app/dashboard`: Admin statistics and cohort reports.
- **Security:** Password hashing with `Werkzeug`, CSRF protection with `Flask-WTF`, and sandboxed HTML previews for EML files.

## Building and Running

### Local Development (Recommended)
1. **Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
2. **Database (Local):**
   ```bash
   docker run -d -p 8000:8000 amazon/dynamodb-local
   export DYNAMODB_ENDPOINT=http://localhost:8000
   python seed_dynamodb.py
   ```
3. **Execution:**
   ```bash
   python run.py
   ```
   The app will be available at `http://localhost:5000`.

### Docker Environment
```bash
docker compose up -d --build
docker compose exec web python seed.py
```
Access at `http://localhost` (port 80).

### Build for Lambda
```bash
make lambda
# or
./scripts/build_lambda.sh
```
This generates `lambda.zip` containing the app and all dependencies in the `package/` directory.

## Testing and Quality
- **Unit/Integration Tests:** Uses `pytest` and `moto` to mock AWS services.
  ```bash
  make test
  ```
- **Linting:** Follows PEP 8 guidelines.
  ```bash
  make lint
  ```

## Development Conventions
- **Naming:** Follow standard Python (snake_case) for functions/variables and PascalCase for classes.
- **Models:** Add new DynamoDB interactions in `app/models.py`. Always use the `_get_table` helper to ensure correct configuration.
- **Blueprints:** When adding new features, create a new blueprint in `app/` and register it in `app/__init__.py`.
- **Infrastructure:** All AWS resources are managed in the `terraform/` directory. Do not create resources manually in the AWS Console.
- **Templates:** Use the base layout `app/templates/base.html` and include accessibility-friendly Bootstrap components.

## Key Files
- `app/models.py`: Data access layer for DynamoDB.
- `app/inspector/routes.py`: Logic for parsing `.eml` files.
- `lambda_handler.py`: Entry point for AWS Lambda.
- `terraform/main.tf`: Main infrastructure definition.
- `config.py`: Environment-based configuration management.
