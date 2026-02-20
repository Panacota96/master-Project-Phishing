# GDPR Compliance & Data Privacy Report

This document outlines how the Phishing Awareness Training Application handles data collection, storage, and security in alignment with the General Data Protection Regulation (GDPR).

## 1. Data Categories & Collection

The application processes two main categories of data:

### A. Personally Identifiable Information (PII)
- **Username**: Used as the primary unique identifier for student accounts.
- **Email Address**: Used for account verification and administrative communication.
- **Password**: Stored exclusively as a cryptographically secure hash (never in plain text).

### B. Educational & Cohort Data
- **Cohort Metadata**: Class name, academic year, and major. This is used for aggregate analytics.
- **Performance Data**: Quiz scores, completion timestamps, and specific question responses.
- **Threat Analysis Logs**: Student classifications of phishing emails and identified signals.

## 2. Data Minimization & Purpose Limitation

In accordance with Article 5 of the GDPR, we adhere to the following:
- **Purpose**: Data is collected solely for the educational purpose of phishing awareness training and academic performance tracking.
- **Minimization**: We do not collect phone numbers, physical addresses, or sensitive personal data (e.g., health, religion, political affiliation).
- **Placeholder Cleaning**: The "Email Threat Inspector" automatically replaces real-world placeholders (like `{{.FirstName}}` or `{{.URL}}`) with generic values to prevent the accidental exposure of third-party personal data within training samples.

## 3. Data Security & Integrity

We implement robust technical and organizational measures (Article 32) to protect data:

### Technical Measures
- **Encryption in Transit**: All communication between the client browser and the AWS Lambda backend is encrypted using **TLS 1.2+** via Amazon API Gateway.
- **Encryption at Rest**: Data stored in **AWS DynamoDB** and **Amazon S3** is encrypted at rest using industry-standard AES-256 encryption.
- **Secure Hashing**: Passwords are hashed using the **PBKDF2** algorithm with a minimum of 600,000 iterations via the `Werkzeug` security library.
- **Identity & Access Management (IAM)**: The backend application operates under a "Least Privilege" IAM role, restricting access only to the specific database tables and S3 prefixes required for its function.

### Privacy by Design
- **Anonymous Inspector Data**: A dedicated `DYNAMODB_INSPECTOR_ANON` table stores classification attempts without linking them to specific usernames. This allows for long-term dataset analysis without maintaining PII links.
- **Sandboxed Execution**: Phishing email previews are rendered in a sandboxed `<iframe>` with `allow-same-origin` restricted, preventing potential malicious scripts from accessing session cookies or local storage.

## 4. User Rights (Data Subject Rights)

Under GDPR, users have the following rights:
- **Right to Access**: Users can view their quiz history and performance directly on their dashboard.
- **Right to Rectification**: Admins can update user metadata (class, major) through the Admin Dashboard.
- **Right to Erasure ("Right to be Forgotten")**: Admins have the capability to delete user accounts and all associated performance data from the database.
- **Right to Data Portability**: Administrators can export cohort and performance data in CSV format for academic reporting.

## 5. Storage Limitation

Data is retained only for the duration of the training course or academic year. Periodic purges of the `dev` environment are performed to ensure outdated training data is not maintained indefinitely.

---
*Last Updated: February 2026*
