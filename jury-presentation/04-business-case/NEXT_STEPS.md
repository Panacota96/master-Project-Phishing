# Next Steps & Roadmap — En Garde

**Current version:** v1.2.3 (deployed, March 2026)
**Document scope:** Immediate production-readiness gaps + short/medium-term product roadmap + The Ask

---

## Immediate — Pre-Production Hardening (< 2 weeks)

These are infrastructure configuration changes that close known security and reliability gaps. Each is 1–2 Terraform PRs.

### 1. AWS WAF v2 on CloudFront (Critical)

**Why:** The login endpoint (`/auth/login`) and quiz submission endpoints are exposed to credential-stuffing and layer-7 floods without rate limiting. The CloudFront distribution currently has no Web ACL.

**What:** Add `aws_wafv2_web_acl` (us-east-1 scope, associated with CloudFront) with:
- `AWSManagedRulesCommonRuleSet` (OWASP Top 10 patterns)
- `AWSManagedRulesKnownBadInputsRuleSet` (Log4j, path traversal)
- Rate-based rule: 300 requests per 5 minutes per IP

**Source:** `documentation/AWS_IMPROVEMENTS.md` §1.1

### 2. Move SECRET_KEY to AWS Secrets Manager (Critical)

**Why:** Flask's `SECRET_KEY` is currently stored as a plaintext Lambda environment variable — visible to anyone with `lambda:GetFunctionConfiguration`. The GitHub Actions runner also writes it to a `.tfvars` file.

**What:** Create `aws_secretsmanager_secret` for `SECRET_KEY`. Update Lambda execution role with `secretsmanager:GetSecretValue`. Update `config.py` to fetch at startup.

**Source:** `documentation/AWS_IMPROVEMENTS.md` §1.4

### 3. Enable DynamoDB Point-in-Time Recovery (High)

**Why:** A mistaken bulk delete or a bug in a migration script could irreversibly destroy quiz attempt history. PITR provides a 35-day rolling recovery window at negligible cost.

**What:** Add `point_in_time_recovery { enabled = true }` to the 3 critical tables: `users`, `attempts`, `responses`.

**Source:** `documentation/AWS_IMPROVEMENTS.md` §2.1

### 4. Custom Domain Activation

**Why:** Sharing a CloudFront URL for a jury presentation is unprofessional. A custom domain signals production intent.

**What:** Activate `engarde.esme.fr` (or equivalent). Configure Route 53 CNAME → CloudFront distribution. Add ACM certificate (already provisioned in Terraform if `var.domain_name` is set).

---

## Short-Term — v1.3 Roadmap (0–3 months)

### Amazon Bedrock AI Coach

**What:** After completing the Quiz or Email Inspector, students can ask the AI coach to explain *why* a particular signal makes an email suspicious. Uses Claude 3 Haiku via Amazon Bedrock API.

**Architecture:** New Lambda function invoked via API Gateway. Prompt includes the email's content and the ground-truth explanation from the answer key. Streamed response rendered in the UI.

**Value:** Transforms passive feedback into a conversational learning moment. Directly differentiates from all competitors.

**Source:** `documentation/FEATURE_PROPOSALS.md` Feature B

### Admin Password Reset UI

**What:** Admins can reset any student's password from the User Management table without deleting and recreating the account.

**Why already mostly built:** `update_user_password()` already exists in `app/models.py`. The route, form, and template are designed in `documentation/FEATURE_PROPOSALS.md`.

**Effort:** 2–3 hours of implementation.

**Source:** `documentation/FEATURE_PROPOSALS.md` Feature A

### Mobile-Responsive Redesign

**What:** The Email Inspector uses an `<iframe>` for HTML preview that breaks on mobile viewports. The quiz flow is partially responsive but requires testing at 375px width.

**Fix:** Replace iframe-based preview with a sandboxed `<div>` rendering approach. Audit all templates against a 375px breakpoint.

### LMS Integration (Moodle / Canvas)

**What:** Report quiz completion and scores to an external LMS grade book via LTI or a REST webhook. Enables En Garde to be embedded as a graded activity in an existing course.

**Architecture:** On quiz completion, publish a score event to SQS → Lambda worker sends LTI Advantage score update to the LMS.

---

## Medium-Term — v2.0 Roadmap (3–6 months)

### Multi-Language Support (French First)

- Flask-Babel for i18n; all UI strings in `.po` files
- French-language email corpus (phishing emails in French have distinct social engineering patterns — not a translation of the English corpus)
- French UI localisation estimated at 6 weeks including corpus extension

### Automated Phishing Corpus Updater

**What:** A scheduled Lambda function that polls public threat intelligence feeds (OpenPhish, PhishTank API, APWG eCrime) for new phishing URLs and email templates. New samples are proposed to admins for classification review before entering the live pool.

**Value:** Corpus stays current with emerging campaigns without manual curation.

### SCORM Export

**What:** Export quiz modules as SCORM 1.2 or 2004 packages for import into any SCORM-compliant LMS.

**Value:** Eliminates the need for API-level LMS integration — schools can import En Garde content the same way they import any off-the-shelf training module.

### Leaderboard & Gamification Layer

**What:** School-wide and cohort-level leaderboards for Inspector accuracy and quiz scores. Weekly "Phishing Threat Report" email sent to students showing their rank.

**GDPR note:** Leaderboards display only opt-in students. Rank, not score, is displayed publicly.

---

## The Ask — What We Need

### Option 1 — Pilot Partner (Primary Ask)

> A company or academic institution willing to run En Garde with their team or students for one semester.

**What you get:**
- Free access for 12 months
- Branded instance (your logo, your domain)
- Direct input on the v1.3 roadmap
- Priority support (response within 24 hours)

**What we get:**
- Real-world usage data (cohort risk score deltas, quiz pass rates, Inspector accuracy improvement)
- A reference customer and co-authored case study
- Testimonial for sales materials

**Ideal pilot partner profile:**
- 50–500 students or employees
- Existing IT security awareness gap (known, not hypothetical)
- Someone with authority to approve a software pilot (IT director, academic director, RSSI)

### Option 2 — Technical Partnership

> A cybersecurity consulting firm interested in white-labeling En Garde for their client security awareness programs.

Revenue share: 80/20 (En Garde / Partner).

### Option 3 — Advisory

> An industry professional willing to give 2 hours of feedback on the product and go-to-market strategy.

No financial commitment. Valuable for roadmap validation and introduction network.

---

## Contact

For pilot inquiries, reach the En Garde team through ESME faculty contacts or via the GitHub repository.
