# Operator Documentation Index

This folder contains resources for DevOps engineers and system administrators managing the Phishing Awareness Training infrastructure.

## Key Resources
- [**INFRASTRUCTURE.md**](INFRASTRUCTURE.md): Detailed AWS resource mapping, IAM roles, and Terraform configuration.
- [**CICD.md**](CICD.md): GitLab CI/CD pipeline overview, environment variables, and deployment stages.
- [**DEPLOYMENT.md**](DEPLOYMENT.md): Procedures for initial and regular deployments, Lambda packaging, and environment management.
- [**MAINTENANCE.md**](MAINTENANCE.md): Database migrations, backups, user management, and troubleshooting common issues.

## Environments
- **Dev**: Automatic deployment from the `main` branch.
- **Prod**: Manual deployment trigger from GitLab CI.
