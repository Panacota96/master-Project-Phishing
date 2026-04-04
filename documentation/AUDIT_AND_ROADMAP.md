# Project Audit & Future Roadmap (April 2026)

This document provides a comprehensive overview of the current feature set of the Phishing Awareness Training Application and outlines the strategic roadmap for future enhancements.

## 1. Feature Audit: Current Capabilities

### 🎓 Student Experience
- **Interactive Learning Path**: 10-question quizzes covering modern attack vectors (URL analysis, Whaling, CEO Fraud, Smishing, etc.).
- **Video-Gated Modules**: Mandatory training videos that must be watched before a student can attempt a quiz.
- **Email Threat Inspector**: A sandbox tool for analyzing a dataset of 98 real-world `.eml` samples with full header, body, and link inspection.
- **Immediate Educational Feedback**: Real-time justifications and pedagogical explanations displayed after every classification.
- **Gamified Progress Tracking**:
    - **Custom Ranks**: Automated progression from "Novice" to "Cyber Sentinel" based on scores.
    - **Visual Progress**: Real-time completion bars on the student history page.
- **Integrated Feedback**: Global "Report Bug" system available on every page.

### 🛠️ Administrative & Operational Tools
- **Full User Lifecycle Management**: Admin UI to view, filter, and delete student accounts.
- **Admin-Side Password Reset (IMPLEMENTED — M2)**: Admins can reset any student's password directly from the user management table without deleting and recreating the account. A per-user modal form enforces the same password-strength policy as the student self-service flow (`app/dashboard/forms.py`, `POST /dashboard/users/<username>/set-password`).
- **Inspector Ground-Truth Dashboard**: Dedicated view to verify the "Answer Key" and preview how the parser handles specific emails.
- **Editable Answer Key (IMPLEMENTED)**: Admins can override any email's classification (Phishing/Spam) and required signals directly from the UI. Overrides are stored in DynamoDB (`DYNAMODB_ANSWER_KEY_OVERRIDES`) and take effect immediately without a code deployment. The static `answer_key.py` remains the fallback baseline.
- **Dynamic Signal Count (IMPLEMENTED)**: Required signal count per email is driven by the answer key (`len(signals)`), not hardcoded. Student UI and server-side validation both respect this dynamically.
- **Advanced Analytics**:
    - **Signal Accuracy Heatmap**: Visual Polar Chart identifying which phishing tactics (e.g., Punycode, Spoofing) are most misunderstood.
    - **Cohort Reporting**: Automated CSV generation filtered by Class, Major, and Academic Year.
- **Bulk Data Operations**: CSV import tools for large cohorts and bulk reset capabilities for retakes.

### 🔐 Authentication & SSO
- **Microsoft 365 / Azure AD SSO (IMPLEMENTED — M4)**: Optional MSAL OIDC integration. When `MSAL_CLIENT_ID` and `MSAL_CLIENT_SECRET` environment variables are set a "Sign in with Microsoft" button appears on the login page (`/auth/sso/login` → `/auth/sso/callback`). The callback auto-provisions a local account on first login. SSO users cannot use local-password login. The admin group can be mapped via `MSAL_ADMIN_GROUP_ID`. See `app/auth/sso.py`.
- **Local Password Login**: Flask-Login with Werkzeug hashing; unchanged and fully backward-compatible.

### 🔒 Security, Privacy & DevOps
- **GDPR by Design**: Anonymous data tables for threat analysis and aggregated cohort-level reporting.
- **Automated Privacy Cleaning**: Regex-based "Placeholder Cleaning" that scrubs PII from training emails.
- **Serverless Architecture**: AWS Lambda + API Gateway + encrypted DynamoDB/S3.
- **SecDevOps Pipeline**: GitHub Actions CI/CD with mandatory linting, unit tests, and infrastructure-as-code (Terraform).

---

## 2. Strategic Roadmap: Future Improvements

### 📈 Phase 1: Content & UX (Short-Term)
- **MFA Fatigue Simulation**: New quiz modules focusing on 2025-2026 trends like push-notification spam and session token theft.
- **Local Asset Hosting**: Migrate brand logos to a local directory to ensure rendering stability without external dependencies.
- **Mobile App Wrapper**: Adapt the responsive UI for a PWA (Progressive Web App) experience.

### 🛡️ Phase 2: Security & Governance (Mid-Term)
- **Admin MFA**: Implement TOTP (Time-based One-Time Password) for all accounts with administrative privileges.
- **Automated Dependency Audits**: Integrate `pip-audit` or `safety` into the GitHub Actions CI pipeline to detect vulnerable libraries.
- **Penetration Testing**: Conduct a "Grey Box" security audit and document findings in a formal security report.

### 🚀 Phase 3: Advanced Intelligence (Completed & Ongoing)
- **Vulnerability Risk Scoring (IMPLEMENTED)**: Automated calculation of cohort-level risk based on signal identification failure rates and knowledge gaps.
- **Adaptive Difficulty Engine**: Dynamically serve harder emails to students who maintain a high identification rate.
- **AI-Generated Content**: Fully integrate the `phishing-content-creator` skill to allow admins to generate infinite new training scenarios via the UI.

---
*Last Updated: February 27, 2026*
