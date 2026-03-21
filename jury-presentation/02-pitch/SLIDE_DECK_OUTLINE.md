# Slide Deck Outline — En Garde Pitch

**Format:** 6 slides · 10 minutes total · Shark Tank style
**Tools:** PowerPoint / Google Slides / Canva (export PDF as backup)
**Aspect ratio:** 16:9

---

## Slide 1 — The Hook

**Presenter:** Person A | **Time:** ~1 min

### Headline
> "Every 11 seconds, a company is hit by a cyberattack. The door they walk through? Your inbox."

### Visual
Full-bleed dark background. A single glowing envelope icon center-screen. Numbers animate in one by one.

### Content
Three stat callouts (large white text, amber numbers):

- **3.4 billion** phishing emails sent — every single day
- **90%** of all data breaches start with one phishing click *(IBM X-Force 2024)*
- **€4.5 million** — the average cost of that one click *(IBM Cost of a Data Breach 2024)*

### Speaker Notes
> "Good morning. I want you to imagine you received an email from your bank this morning. It looked perfect — the logo, the layout, the urgent tone. You clicked. Game over. You just handed attackers the keys to your company. This is happening 3.4 billion times a day. And the people clicking are not stupid — they are simply untrained. That is the problem we are here to solve. We are En Garde."

---

## Slide 2 — The Problem

**Presenter:** Person A | **Time:** ~1.5 min

### Headline
> "Engineering students are the future workforce. Today, they're the weakest link."

### Visual
Split: left side — tired student staring at a boring PDF slideshow. Right side — red "DATA BREACH" notification on a laptop.

### Content
**Three problem statements:**

1. **No retention** — Annual compliance slideshows are forgotten within 72 hours. Zero active learning.
2. **No cohort tooling** — Existing platforms (KnowBe4, Proofpoint) are built for enterprise IT teams, not academic cohorts. No class-level analytics, no professor view.
3. **No real practice** — Reading about phishing does not build muscle memory. Students need to interact with real threats.

**The gap:**
> No platform exists that combines hands-on phishing simulation, cohort-level analytics, and GDPR-compliant storage — built specifically for engineering schools.

### Speaker Notes
> "ESME students will graduate into companies where they handle sensitive data on day one. But what training do they get today? A PDF. Maybe a video. Then a checkbox. Research shows retention drops to near zero after 72 hours without active practice. And the tools that DO work — like KnowBe4 — cost €30 per user per year and require a dedicated IT team to run. Schools can't afford that, and they shouldn't have to."

---

## Slide 3 — Our Solution: En Garde

**Presenter:** Person A | **Time:** ~2 min

### Headline
> "En Garde — hands-on phishing awareness training, built for engineering schools."

### Visual
Three-panel strip showing the app:
- Panel 1: Quiz results page with "Threat Hunter" badge
- Panel 2: Email Inspector with parsed email headers and signal checkboxes
- Panel 3: Admin dashboard with cohort risk scores

**Live app URL displayed prominently at bottom.**

### Content
**Feature 1 — Quiz System**
- Video-gated training modules (can't skip the learning)
- Multiple-choice quizzes with detailed explanations for every answer
- Rank badge system: "Aware" → "Defender" → "Threat Hunter"

**Feature 2 — Email Inspector**
- 98 real-world phishing and spam emails from enterprise threat libraries
- Students classify each email and identify attack signals (impersonation, urgency, fake login, etc.)
- Immediate scored feedback with explanations

**Feature 3 — Admin Dashboard**
- Cohort risk scoring — see which classes are most vulnerable at a glance
- Live answer key editor — update phishing ground truth without touching code
- CSV bulk import — onboard 200 students in 2 minutes

### Speaker Notes
> "So we built En Garde. Three features that work together. First — a quiz system with real training videos and ranked badges. Second — the Email Inspector, where students analyze 98 real phishing emails and identify attack signals the way a SOC analyst would. Third — the admin dashboard, where professors see which cohorts are struggling and can update the answer key when new threats emerge. No IT team required."

---

## Slide 4 — The Tech Edge

**Presenter:** Person B | **Time:** ~1.5 min

### Headline
> "Serverless. Scalable. GDPR-native. Deploy in under 10 minutes."

### Visual
Simplified AWS architecture diagram:
`Browser → CloudFront → API Gateway → Lambda → DynamoDB / S3`

### Content
**4 technical differentiators:**

| Advantage | Detail |
|-----------|--------|
| Serverless | AWS Lambda + DynamoDB: scales from 10 to 10,000 students with zero infrastructure management |
| Cost | ~€0.02 per student per month — 95%+ lower than traditional SaaS hosting |
| GDPR-native | Inspector submissions stored anonymously (no username linkage) by design |
| IaC | Full Terraform + GitHub Actions OIDC — entire stack deploys in < 10 minutes |

**Admin-editable without code:**
> Answer key overrides stored in DynamoDB — professors update phishing ground truth from the dashboard. No deployment needed.

### Speaker Notes
> "Here's why this scales. The entire platform runs on AWS serverless — Lambda, DynamoDB, S3, CloudFront. No servers to manage, no auto-scaling configuration, no ops team. The AWS bill for a 200-student school is approximately twenty euros a month. That is not a typo. And everything is GDPR-compliant by design — the Inspector never stores a student's username with their answers. Finally, the entire infrastructure is defined in Terraform and deployed via GitHub Actions. Onboarding a new school takes ten minutes."

---

## Slide 5 — Traction & Metrics

**Presenter:** Person B | **Time:** ~1.5 min

### Headline
> "Production-ready. Deployed on AWS. Tested. Monitored."

### Visual
Dashboard of metrics — consider a "scoreboard" design with 6 metric tiles.

### Content
**6 production metrics:**

| Metric | Value |
|--------|-------|
| Version | v1.2.3 — production-deployed on AWS (eu-west-3) |
| Test suite | 64 automated tests (pytest + moto), all passing |
| Email corpus | 98 real phishing/spam emails across 10 attack signal categories |
| Infrastructure | 9 DynamoDB tables, full IaC (Terraform), GitHub Actions CI/CD |
| Monitoring | 6 CloudWatch alarms (Lambda errors, throttles, DynamoDB capacity) |
| Deployment time | < 10 minutes from git push to live |

**Optional:** 30-second demo video clip embedded in slide (autoplay on click).

### Speaker Notes
> "This is not a mockup. En Garde is deployed on AWS in the Paris region, version 1.2.3, with 64 automated tests running on every push and six CloudWatch alarms monitoring the production stack. The email corpus contains 98 real phishing and spam emails covering ten distinct attack signal categories. We built this the way a production engineering team would — infrastructure as code, CI/CD pipeline, monitoring, the works."

---

## Slide 6 — Business Model & The Ask

**Presenter:** Person B | **Time:** ~2.5 min

### Headline
> "€5.3B market. €0.02/user/month cost. ~95% gross margin. We need one pilot partner."

### Visual
Left half: SaaS pricing table. Right half: TAM/SAM/SOM concentric circles.

### Content
**SaaS Pricing:**

| Tier | Price | For |
|------|-------|-----|
| Starter | €2/student/month | Individual professors, bootcamps (≤50 users) |
| Pro | €5/student/month | Engineering schools, 50–500 students |
| Enterprise | Custom (~€3–4k/year) | Large institutions, corporate L&D |

**Market:**
- **TAM:** €5.3B — global security awareness training market (2024), growing 15%/year → €10B+ by 2030
- **SAM:** €600M — European higher education + SME segment
- **SOM (Year 1):** €15M — French grandes écoles + engineering schools

**Unit economics (Pro tier, 200-student school):**
- Revenue: €1,000/month → €12,000/year
- AWS cost: ~€20–50/month
- Gross margin: ~95%

**Go-to-market:**
1. ESME pilot → case study → expand via grandes écoles network
2. Corporate L&D channel via cybersecurity consulting partners

**The Ask:**
> "We are looking for an industry partner — a company or institution willing to run a pilot with their teams or students. You get free access for one year, a branded instance, and direct input on our roadmap. We get real-world validation and a reference customer. That is the deal. Who's in?"

### Speaker Notes
> "The security awareness training market is worth 5.3 billion euros and growing at 15% per year. The enterprise players — KnowBe4, Proofpoint — are expensive and built for corporate IT, not schools. Our unit economics are brutal in the best way: a 200-student school pays us €1,000 a month, our AWS bill is €30. That is 95% gross margin. Our ask is simple: we need one pilot partner. If you run a company or a school, give us your team or your students for one semester. Free. Branded. With you shaping the roadmap. In exchange, we get the case study that opens every other door. So — who wants to be first?"
