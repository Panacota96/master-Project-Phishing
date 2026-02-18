# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.1.1] - 2026-02-18

### Fixed

- GitLab CI: corrected heredoc indentation in destroy jobs to prevent YAML/shell parse errors.
- GitLab CI: seed step now uses a venv to avoid PEP 668 "externally managed" failures.
- GitLab CI: seed step reads Terraform outputs from `terraform/` after `cd ..` to avoid invalid DynamoDB table names.

---

## [1.1.0] - 2026-02-12

### Added

- **Email Threat Inspector** (`/inspector/`) — a standalone email analysis tool modeled after TryHackMe's "Wareville Email Threat Inspector"
  - Sidebar listing all 6 `.eml` files from `examples/` with subject, from, to, and date metadata
  - Full email detail view with: message overview, HTML preview (sandboxed iframe), headers table, extracted links, attachments list, and security warnings
  - Client-side classification form: users classify each email as Spam or Phishing, select phishing signals, and receive immediate correct/incorrect feedback with CTF flags
  - 10 phishing signal categories supported: Impersonation, Typosquatting/Punycodes, External Sender Domain, Spoofing, Social Engineering Text, Sense of Urgency, Fake Invoice, Malicious Attachment, Fake Login Page, Side Channel Communication Attempt
  - Backend EML parsing using Python stdlib (`email` module) — no new dependencies
  - Path traversal protection on the email detail API endpoint
  - Security warnings auto-detected: From/Return-Path domain mismatch, punycode domains in links, suspicious `@` in URLs
- New Flask blueprint: `app/inspector/` with 3 routes (`/inspector/`, `/inspector/api/emails`, `/inspector/api/emails/<filename>`)
- Standalone dark-themed inspector template (does not extend `base.html`)
- "Email Inspector" link added to the main app navbar
- `.eml` files now included in Docker image (`COPY examples/ examples/` in Dockerfile, removed `examples/` from `.dockerignore`)

### Files Created

- `app/inspector/__init__.py` — Blueprint registration
- `app/inspector/routes.py` — API routes and EML parsing logic
- `app/templates/inspector/inspector.html` — Standalone inspector UI (CSS + JS)

### Files Modified

- `app/__init__.py` — Registered inspector blueprint
- `app/templates/base.html` — Added "Email Inspector" navbar link
- `.dockerignore` — Removed `examples/` exclusion
- `Dockerfile` — Added `COPY examples/ examples/`

---

## [1.0.0] - 2026-02-12

### Added

- **Phishing Awareness Quiz App** — Flask web application for phishing awareness training
  - User authentication: register, login, logout with password hashing (Werkzeug)
  - Admin vs regular user roles (`is_admin` flag)
  - Quiz system: list quizzes, take multiple-choice quizzes, view explanations after each question, progress bar, score summary with color-coded feedback
  - Quiz history per user
  - Admin dashboard: stat cards (total users, attempts, average score), score distribution bar chart (Chart.js), per-quiz stats table, recent activity table
  - Seed script (`seed.py`) creating admin user and 10 phishing awareness questions
- **Data models**: User, Quiz, Question, Answer, QuizAttempt (SQLAlchemy + SQLite)
- **Docker support**: Dockerfile (python:3.12-slim + gunicorn), docker-compose.yml (web + Nginx), Nginx reverse proxy config
- **AWS deployment guide**: `aws/README.md` with EC2 Free Tier setup, `user-data.sh` boot script, `env.example` template
- **Real phishing email samples** (`examples/`): 6 `.eml` files from TryHackMe Advent of Cyber lab covering fake invoices, impersonation, urgency, spoofing, punycode, and spam
- **TryHackMe reference materials** (`Phishing AOC/`): CTF flags/answers, download scripts, email inspector source HTML
