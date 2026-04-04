# Compliance & Security Frameworks Report

This document outlines how the Phishing Awareness Training Application addresses key cybersecurity and data privacy frameworks, including GDPR, NIST CSF, OWASP Top 10, and SOC 2.

## 1. GDPR (General Data Protection Regulation)
The application is designed with "Privacy by Design" to comply with EU data protection standards.

### Technical Implementations:
- **Data Minimization (Art. 5)**: Only essential PII (email, username) is collected. Educational data is aggregated by cohort (Class/Year/Major) rather than individual tracking where possible.
- **Anonymization**: The `DYNAMODB_INSPECTOR_ANON` table stores threat classifications without links to specific users, ensuring long-term research data does not contain PII.
- **Security of Processing (Art. 32)**:
    - **Encryption in Transit**: All traffic is served over HTTPS (TLS 1.2+).
    - **Encryption at Rest**: AWS DynamoDB and S3 use AES-256 encryption.
- **Placeholder Cleaning**: Automated regex-based cleaning (`_clean_placeholders`) removes potential third-party PII from real-world email samples before they are displayed to students.

## 2. NIST Cybersecurity Framework (CSF) 2.0
The project aligns with the NIST CSF core functions:

### **Identify & Protect**
- **Asset Management**: All infrastructure is defined as code (Terraform), ensuring a clear inventory of cloud resources.
- **Identity & Access Management (PR.AC)**: 
    - Least-privilege IAM roles for the Lambda execution environment.
    - Secure password hashing using PBKDF2 with high iteration counts.
- **Data Security (PR.DS)**: Implementation of encryption at rest and in transit.

### **Detect & Respond**
- **Logging (DE.AE)**: Centralized logging via Amazon CloudWatch for auditing application errors and security events (e.g., failed logins).
- **Bug Reporting**: A global feedback system allows users to report anomalies, serving as a crowd-sourced detection mechanism.

## 3. OWASP Top 10 (Web Application Security)
We actively mitigate the most critical web risks:

- **A01:2021-Broken Access Control**: 
    - Use of `Flask-Login` for session management.
    - Admin-only routes are protected with role-based checks (`role` in `admin`/`instructor`) and `@login_required`.
- **A02:2021-Cryptographic Failures**: Passwords are never stored in plain text; industry-standard `Werkzeug` hashing is used.
- **A03:2021-Injection**: Use of **AWS DynamoDB** (NoSQL) and parameterized queries via `boto3` mitigates traditional SQL injection.
- **A05:2021-Security Misconfiguration**: Infrastructure is provisioned via Terraform, reducing human error in AWS Console configurations.
- **A07:2021-Identification and Authentication Failures**: Secure session cookies and CSRF protection (Flask-WTF).

## 4. SOC 2 (Trust Services Criteria)
The application architecture addresses the core SOC 2 pillars:

- **Security**: Protected by AWS infrastructure security, IAM policies, and application-level auth.
- **Availability**: Serverless architecture (Lambda + API Gateway) provides high availability and automatic scaling.
- **Confidentiality**: Access to sensitive student data is restricted to authenticated administrators.
- **Privacy**: Adherence to GDPR principles as detailed above.

---
*Last Updated: February 2026*
