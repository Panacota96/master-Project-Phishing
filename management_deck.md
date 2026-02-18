---
marp: true
paginate: true
size: 16:9
---

# Phishing Awareness Training Platform
## Management Briefing

- Serverless AWS deployment
- GDPR-compliant, cohort-based analytics
- Automated CI/CD and reproducible ops

---

# Executive Summary

- Delivered a production-ready phishing awareness platform
- Serverless architecture (Lambda + API Gateway)
- Analytics aggregated by class/year/major (GDPR safe)
- CI/CD validated with GitLab pipeline

---

# Business Goals

- Improve phishing detection skills
- Provide measurable learning outcomes
- Ensure compliance and auditability
- Enable repeatable deployment and scaling

---

# Solution Overview

**Core Features**
- Phishing Quiz with explanations and scoring
- Email Threat Inspector for real `.eml` samples
- Admin analytics + CSV reports

**Compliance**
- Group-only reporting (no individualization)

---

# Architecture (High Level)

- API Gateway → AWS Lambda (Python 3.12)
- DynamoDB for users/quizzes/attempts/inspector
- S3 for `.eml` samples and reports
- GitLab CI/CD pipeline

---

# Data & GDPR Model

- User identities only for authentication
- Analytics by cohort: class + academic year + major
- Reports exported as aggregated CSVs

---

# Deployment & Ops

- Terraform IaC with remote state (S3 + DynamoDB lock)
- Dev/prod environment separation
- Reproducible runbooks + screenshot checklist

---

# CI/CD Pipeline

Stages:
- Lint → Test → Build → Plan → Deploy (manual)
- JUnit test reports uploaded
- Secrets via GitLab CI variables

---

# Current Status

- Dev environment deployed and verified
- EML samples uploaded
- DynamoDB seeded
- CI/CD pipeline green

---

# Risks & Mitigations

- IAM permissions: dedicated deploy user
- Secrets: GitLab masked variables
- Drift: Terraform-controlled state

---

# Next Steps

- Production deployment runbook
- Cohort trend dashboards
- Monthly automated reporting
- Security review + least privilege refinement

---

# Thank You

Questions?
