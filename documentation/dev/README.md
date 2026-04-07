# Developer Documentation Index

This folder contains resources for developers contributing to the Phishing Awareness Training Application.

## Key Resources
- [**ARCHITECTURE.md**](ARCHITECTURE.md): Technical deep-dive into the Flask app structure, DynamoDB models, and data flow.
- [**SETUP.md**](SETUP.md): Instructions for local development, virtual environment setup, and database seeding.
- [**CONTRIBUTING.md**](CONTRIBUTING.md): Coding standards, testing requirements, and Git branching strategy.
- [**TESTING_GUIDE.md**](TESTING_GUIDE.md): Running the test suite, mocking AWS with moto, and post-deployment verification.
- [**REALISM_GUIDE.md**](REALISM_GUIDE.md): Tips for making phishing and spam simulations more realistic.
- [**ADDING_QUIZZES.md**](ADDING_QUIZZES.md): How to add new quiz questions and video lessons.
- [**ADDING_EML_FILES.md**](ADDING_EML_FILES.md): How to add new .eml samples to the Email Threat Inspector.

## Tech Stack
- **Backend**: Flask (Python 3.12), Flask-Login, Flask-WTF.
- **Database**: DynamoDB (AWS NoSQL) using `boto3`.
- **Frontend**: Jinja2, Bootstrap 5, Chart.js.
- **Infrastructure**: Terraform, AWS Lambda, S3, API Gateway.
