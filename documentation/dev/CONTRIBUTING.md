# Contributing Guide - Phishing Awareness Training

Thank you for contributing to the Phishing Awareness Training project! This guide outlines our development standards and how to submit your changes.

## Development Principles
- **Modularity**: New features should be added as Flask blueprints or model methods in `app/models.py`.
- **Consistency**: Follow standard Python (snake_case) for functions/variables and PascalCase for classes.
- **Simplicity**: Avoid complex abstractions unless necessary; prefer readable, explicit code.
- **Security**: Never commit secrets or API keys. Use environment variables for configuration.

## Coding Standards
- **Python**: Follow **PEP 8** guidelines. Use `make lint` to check your code.
- **Flask**: Use the application factory pattern and register new blueprints in `app/__init__.py`.
- **Database**: Add new DynamoDB interactions in `app/models.py`. Always use the `_get_table` helper.
- **Templates**: Extend `app/templates/base.html` and use Bootstrap 5 for all UI components.

## Testing Requirements
All new features and bug fixes must be accompanied by relevant tests:
- **Unit/Integration Tests**: Use `pytest` and `moto` for mocking AWS services.
- **Run Tests**: Use `make test`.
- **Validation**: For changes to `.eml` samples, run `make validate-eml`.

## Branching Strategy
- **`main`**: The production branch (protected).
- **`dev`**: The default development branch.
- **Feature Branches**: Create feature-specific branches (e.g., `feature/new-quiz-type`) and submit a Merge Request (MR) in GitLab for review.

## Pull Request (Merge Request) Process
1. Ensure your branch is up-to-date with `dev`.
2. Run all tests (`make test`) and linting (`make lint`).
3. Describe the changes in the MR description, including any new environment variables or infrastructure updates.
4. Request a review from the maintainers.

## Documentation Standards
When updating the codebase, ensure you also update the relevant documentation in the `documentation/` folder:
- **Architecture**: Update `dev/ARCHITECTURE.md` if the system structure changes.
- **Operator Guides**: Update `operator/` files if infrastructure or deployment steps are modified.
- **User Guides**: Update `user/` files for new features visible to students or admins.
