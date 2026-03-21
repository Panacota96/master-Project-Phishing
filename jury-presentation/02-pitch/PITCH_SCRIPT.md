# Full Pitch Script — En Garde (Shark Tank Style)

**Total time:** 10 minutes
**Format:** Two presenters, Shark Tank framing
**Tone:** Confident, direct, commercial — not academic

---

## PERSON A — Opening Hook (60 seconds)

> "Imagine you receive an email from your bank this morning. It looks perfect. The logo is right. The sender address looks right. The message is urgent — *'Suspicious activity detected. Click here to verify your account within 24 hours or your access will be suspended.'*
>
> You click.
>
> Game over.
>
> You just handed attackers the keys to your company, your bank, your identity. And here is the uncomfortable truth: you are not stupid. You are untrained. This exact scenario plays out **3.4 billion times every single day**.
>
> 90% of all data breaches — from small startups to global banks — start with exactly that one click. The average cost? **€4.5 million**.
>
> We are En Garde, and we are here to make sure that click never happens."

---

## PERSON A — The Problem (90 seconds)

> "Here is the gap we are filling.
>
> ESME students are the future engineers, the future developers, the future data architects of French companies. They will handle sensitive data on day one of their careers. But what cybersecurity training do they receive today?
>
> A PDF. Maybe a 20-minute video they can skip. Then a checkbox that says 'I have read and understood the security policy.' That is it.
>
> Research is unambiguous: information retention from passive reading drops to near zero within 72 hours unless it is reinforced by active practice. Annual compliance training does not change behavior. It creates the illusion of safety.
>
> Now, there are tools that DO work — platforms like KnowBe4 and Proofpoint that run real phishing simulations. But they cost €30 to €60 per user per year, require a dedicated IT security team to operate, and are designed for enterprise corporations — not for a professor managing 200 students across three cohorts.
>
> There is no platform built for cohort-based academic training. No class-level analytics for professors. No admin-editable threat library. No GDPR-compliant architecture. No sub-€5-per-user pricing.
>
> Until now."

---

## PERSON A — The Solution (2 minutes)

> "We built En Garde — a hands-on phishing awareness training platform built specifically for engineering schools.
>
> Three features. Let me walk you through them.
>
> **Feature one: the Quiz System.** Students watch a training video — they cannot skip it, that is enforced. Then they take a multiple-choice quiz. Every wrong answer comes with a detailed explanation of why it was wrong. And every student earns a rank badge based on their performance — from 'Aware' to 'Threat Hunter'. Gamification works. Passive reading does not.
>
> **Feature two: the Email Inspector.** This is our crown jewel. Students are presented with a pool of 8 real-world emails — drawn from a corpus of 98 real phishing and spam emails from enterprise threat libraries. They must classify each one — Phishing or Spam — and identify the specific attack signals: is it impersonation? Urgency manipulation? A fake login page? A punycode domain attack? Then they submit, and they get immediate scored feedback explaining exactly what they missed and why. This is active learning. This is muscle memory.
>
> **Feature three: the Admin Dashboard.** Professors log in and see their cohort risk scores — which classes are most vulnerable, who needs re-training, and where. There is a live answer key editor, so when a new phishing technique emerges — a new Amazon AWS impersonation campaign, a Slack-based credential harvester — the professor updates the answer key from the dashboard. No code deployment. No IT ticket. Done in two minutes."

---

## PERSON B — The Tech Edge (90 seconds)

> "Now let me talk about what makes this platform commercially viable and technically credible.
>
> En Garde runs entirely on AWS serverless infrastructure. AWS Lambda, DynamoDB, S3, CloudFront. There are no servers to manage. No auto-scaling configuration. No DevOps team required. The platform scales automatically from 10 students to 10,000 students.
>
> What does that cost? Approximately **€0.02 per student per month** on AWS. Not per year. Per month.
>
> We built GDPR compliance in from the start, not bolted on later. The Email Inspector stores anonymous interaction data — student answers are never linked to a username in the inspector table. Privacy-by-design, not privacy-by-policy.
>
> The admin answer key editor is a genuine differentiator. Phishing techniques evolve weekly. With traditional platforms, updating threat scenarios requires a software deployment cycle — days or weeks. With En Garde, a professor opens the dashboard, edits the answer key, and the change is live in seconds. No IT involvement. No code change.
>
> The entire infrastructure is defined in Terraform and deployed via GitHub Actions with OIDC authentication. A new school environment — new AWS account, new DynamoDB tables, new CloudFront distribution — takes under 10 minutes to provision. That is how you scale to 50 schools without an operations team."

---

## PERSON B — Traction & Metrics (90 seconds)

> "Let me give you the numbers.
>
> En Garde is live. Version 1.2.3 deployed on AWS in the Paris region — eu-west-3 — as we speak.
>
> **64 automated tests** run on every single git push. pytest with mocked AWS services. The CI/CD pipeline catches regressions before they reach production.
>
> **98 real-world emails** in the inspector corpus — phishing and spam samples covering **10 distinct attack signal categories**: impersonation, urgency manipulation, fake login pages, punycode domain attacks, side-channel tracking, social engineering, and more.
>
> **9 DynamoDB tables** managing users, quiz attempts, per-question responses, inspector submissions, cohort data, and admin overrides — with proper GSIs for analytics queries.
>
> **6 CloudWatch alarms** monitoring Lambda error rates, throttling, and DynamoDB capacity — with SNS notification integration.
>
> Full infrastructure-as-code. Full CI/CD. Full monitoring. This is not a student project running on a laptop. This is a production-grade system."

---

## PERSON B — Business Model & The Ask (2.5 minutes)

> "Let's talk business.
>
> The global security awareness training market is worth **€5.3 billion** in 2024 and growing at 15% per year. It will hit €10 billion by 2030. The incumbents — KnowBe4, Proofpoint, Cofense — are all US-based enterprise-first players with minimum contract sizes that exclude academic institutions entirely.
>
> Our target: European engineering schools, grandes écoles, and SMEs that need affordable, cohort-aware training. That is a **€600 million SAM** in Europe. In France alone — grandes écoles, engineering schools, BTS programs — we estimate a **€15 million Year 1 opportunity**.
>
> Our model is SaaS licensing:
>
> - **Starter tier** at €2 per student per month — for individual professors and bootcamps.
> - **Pro tier** at €5 per student per month — for schools with 50 to 500 students. Full dashboard, CSV import, cohort analytics.
> - **Enterprise** at a custom flat rate — for large institutions and corporate L&D.
>
> Let me show you the unit economics on Pro. A 200-student school pays us €1,000 per month — €12,000 per year. Our AWS cost for that school: approximately €30 per month. Gross margin: **95%**.
>
> Our go-to-market is simple. Phase 1: ESME pilot. Real students, real results, real case study. Phase 2: use that case study to expand through the grandes écoles network — CentraleSupélec, Arts et Métiers, INSA. Phase 3: corporate L&D channel through cybersecurity consulting partners.
>
> **The Ask.**
>
> We are not here asking for money today. We are asking for something more valuable: a pilot partner.
>
> If you run a company or an institution — if you have a team of engineers, students, or employees who will face phishing attempts in their careers — give us one semester. Free access. A branded instance of En Garde. Direct input on our product roadmap.
>
> In exchange, we get real-world validation and a reference customer that opens every other door.
>
> The deal is simple. The upside is asymmetric. Who wants to be first?"

---

## Closing (5 seconds)

> *[Both presenters stand, confident.]*
>
> "We are En Garde. Thank you."
