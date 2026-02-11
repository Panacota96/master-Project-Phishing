# Master-Project-Phishing

A **phishing awareness training web application** built with Flask, created as part of the ESME engineering school Cloud SecDevOps course (TP1/TP2).

Users take interactive quizzes to learn how to identify phishing emails, and can inspect real-world phishing samples using the built-in Email Threat Inspector.

## Features

### Phishing Quiz
- Multiple-choice quizzes covering phishing techniques (URL analysis, spoofing, urgency tactics, CEO fraud, smishing, MFA, etc.)
- Explanations after each question showing why an email is phishing or legitimate
- Progress bar, color-coded score summary, and quiz history per user

### Email Threat Inspector
- Standalone tool at `/inspector/` for analyzing real `.eml` files
- Parses and displays: message overview, full headers, HTML preview (sandboxed), extracted links, attachments, and security warnings
- Users classify each email as Spam or Phishing and select phishing signals
- Immediate feedback with correct/incorrect indicators and CTF flags
- 10 phishing signal categories: Impersonation, Typosquatting/Punycodes, External Sender Domain, Spoofing, Social Engineering, Urgency, Fake Invoice, Malicious Attachment, Fake Login Page, Side Channel Communication

### Admin Dashboard
- Stats overview: total users, total attempts, average score
- Score distribution bar chart (Chart.js)
- Per-quiz statistics and recent activity tables

### Authentication
- Register / Login / Logout with form validation
- Password hashing (Werkzeug)
- Admin vs regular user roles

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask (Python 3), Flask-SQLAlchemy, Flask-Login, Flask-WTF |
| Database | SQLite |
| Frontend | Jinja2 + Bootstrap 5 (CDN) |
| Charts | Chart.js |
| EML Parsing | Python `email` stdlib (no extra dependencies) |
| Deployment | Docker + Gunicorn + Nginx |

## Quick Start (Local)

```bash
# Install dependencies
pip install -r requirements.txt

# Seed the database with admin user + quiz questions
python seed.py

# Run the development server
python run.py
```

The app runs at **http://localhost:5000**. Default admin: `admin` / `admin123`

## Docker

```bash
# Build and start (Nginx on port 80 -> Gunicorn -> Flask)
docker compose up -d --build

# Seed the database
docker compose exec web python seed.py

# Stop
docker compose down
```

Access at **http://localhost** (port 80).

## AWS Deployment

See [aws/README.md](aws/README.md) for a full guide to deploy on AWS Free Tier (EC2 t2.micro + Docker + Nginx).

## Project Structure

```
master-Project-Phishing/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # User, Quiz, Question, Answer, QuizAttempt
│   ├── auth/                # Login, register, logout
│   ├── quiz/                # Quiz list, take quiz, results, history
│   ├── dashboard/           # Admin stats and charts
│   ├── inspector/           # Email Threat Inspector (EML parsing + API)
│   ├── templates/           # Jinja2 templates (base, auth, quiz, dashboard, inspector)
│   └── static/css/          # Custom styles
├── examples/                # 6 real phishing/spam .eml samples
├── Phishing AOC/            # TryHackMe lab reference materials
├── aws/                     # AWS deployment guide and scripts
├── nginx/                   # Nginx reverse proxy config
├── Dockerfile               # Python 3.12-slim + Gunicorn
├── docker-compose.yml       # Web + Nginx services
├── seed.py                  # Database seeder (admin + 10 questions)
├── config.py                # App configuration
├── run.py                   # Entry point
├── requirements.txt         # Python dependencies
├── CHANGELOG.md             # Version history
└── CLAUDE.md                # AI assistant context
```

## Email Samples

Six real `.eml` files from TryHackMe's Advent of Cyber phishing lab:

| Email | Type | Signals |
|-------|------|---------|
| Fake Invoice | Phishing | Fake Invoice, Urgency, Spoofing |
| Impersonation + Attachment | Phishing | Impersonation, Malicious Attachment, Spoofing |
| Impersonation + Urgency | Phishing | Impersonation, Social Engineering, Urgency |
| Legit App Impersonation | Phishing | Impersonation, External Domain, Social Engineering |
| Marketing Spam | Spam | N/A |
| Punycode Attack | Phishing | Punycode, Impersonation, Social Engineering |

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

CC0
