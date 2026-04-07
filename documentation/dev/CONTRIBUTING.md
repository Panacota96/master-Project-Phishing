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
- **Inspector Parsing Tests**: Run `pytest tests/test_inspector_parsing.py` to verify all `.eml` samples are correctly viewed and placeholders cleaned.
- **Run Tests**: Use `make test`.
- **Validation**: For changes to `.eml` samples, run `make validate-eml`.

## Branching Strategy
- **`main`**: The production branch (protected).
- **Short-lived branches**: Branch from `main` using `fix/<issue-number>-<slug>`, `feature/<milestone-slug>`, `docs/<slug>`, or `chore/<slug>`.
- **Pull requests**: Open a PR back to `main` for every change, even for solo work, so the required checks and branch protections stay effective.

## Pull Request (Merge Request) Process
1. Branch from the latest `main`.
2. Run the required local checks: `make lint`, `make test`, `make docs-check`, and `terraform -chdir=phishing-platform-infra/terraform validate` when infra changes are involved.
3. Link the backing issue and milestone in the PR description.
4. Update the workboard and affected docs before merging.

## Documentation Standards
When updating the codebase, ensure you also update the relevant documentation in the `documentation/` folder:
- **Architecture**: Update `dev/ARCHITECTURE.md` if the system structure changes.
- **Operator Guides**: Update `operator/` files if infrastructure or deployment steps are modified.
- **User Guides**: Update `user/` files for new features visible to students or admins.
