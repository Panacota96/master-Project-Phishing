# Q&A Preparation — En Garde Jury Pitch

**Format:** 5-minute Q&A after 10-minute pitch
**Anticipated questions:** 15 (jury may ask 3–5 in the allotted time)
**Tone:** Direct, commercial — no hedging, no "that's a great question"

---

## Q1 — "Why would a company pay for this when KnowBe4 has a free tier?"

**Answer:**
> "KnowBe4's free tier gives you 1 phishing simulation template and basic reporting — no cohort analytics, no custom email corpus, no admin-editable answer key, no GDPR-native storage. It's also designed for corporate IT admins, not professors. Our Pro tier at €5/student/month is 80% cheaper than KnowBe4's lowest paid plan and built for exactly the workflow a professor or training manager actually uses. Different product, different buyer, different price point."

---

## Q2 — "How is this different from KnowBe4, Proofpoint, Cofense?"

**Answer:**
> "Three differences: buyer, architecture, cost. KnowBe4 and Proofpoint sell to enterprise security teams — minimum contracts, dedicated IT setup, US data residency. Cofense is simulation-only, no learning layer. We sell to professors and training managers in EU institutions. Serverless AWS in eu-west-3 — data never leaves France. And our all-in AWS cost is €0.02/student/month, which is why we can price at €5 and still have 95% gross margin. The moat is the cohort-aware admin layer and the GDPR architecture — things that take 18 months to build correctly, not 3."

---

## Q3 — "What's your GDPR legal basis for storing student interaction data?"

**Answer:**
> "Legitimate interest under Article 6(1)(f) for aggregate analytics — the institution has a legitimate interest in knowing which cohorts are most vulnerable to phishing. For the Email Inspector specifically, we designed around the privacy-by-design principle: the inspector results table stores anonymous entries only — no username is ever written to the inspector submissions table. Even if the database were breached, you couldn't link a set of wrong answers back to a student. We're also happy to operate under a data processing agreement with the institution as controller."

---

## Q4 — "What happens if a phishing email sample becomes outdated or inaccurate?"

**Answer:**
> "That's exactly why we built the admin answer key editor. The ground truth for every email — its classification and required signals — is stored in DynamoDB, not hardcoded. A professor or admin can log into the dashboard, update any email's answer key in under a minute, and the change is live immediately — no code deployment, no IT ticket. We also have a static fallback in `answer_key.py` for bootstrapping, and the DynamoDB override takes precedence at runtime."

---

## Q5 — "How do you prevent answer sharing between students?"

**Answer:**
> "Two mechanisms. First, the email pool is assembled per-session from a corpus of 98 emails, with randomization baked in — each student gets a different subset. Second, the quiz system enforces one attempt per user per quiz, enforced by a DynamoDB conditional put_item — not just an application-layer check. Sharing answers from the same pool is partially mitigated by signal selection: even if two students get the same email, they each need to select the correct signals independently. Full anti-collusion would require a larger corpus — that's roadmap."

---

## Q6 — "What's the cost per student per month on AWS?"

**Answer:**
> "Approximately €0.02 per student per month. That breaks down to DynamoDB pay-per-request writes (~€0.01), Lambda invocations and GB-seconds (~€0.005), S3 storage and GET requests for EML files (~€0.003), and CloudFront data transfer (~€0.002). At 200 students and typical quiz + inspector usage, the total AWS bill is €20–50 per month. We verified this against the AWS pricing calculator for eu-west-3."

---

## Q7 — "Can this integrate with an existing LMS like Moodle or Canvas?"

**Answer:**
> "Not yet — that's a v1.3 roadmap item. The architecture supports it: quiz completion events are written to DynamoDB with timestamps and scores, so a Moodle plugin could query the En Garde API and report grades back to the LMS grade book. SCORM export is also on the roadmap, which would make integration with any SCORM-compliant LMS a configuration change, not a development project. If a pilot partner has a specific LMS integration requirement, we'd prioritize it."

---

## Q8 — "Why serverless instead of a traditional VPS or SaaS hosting model?"

**Answer:**
> "Three reasons. Cost: pay-per-request DynamoDB and per-invocation Lambda means we pay nothing when no student is using the platform — a school that runs quizzes for 4 weeks and then goes quiet doesn't generate a €300/month EC2 bill. Scale: Lambda scales horizontally and automatically — we don't configure auto-scaling groups. Operations: no SSH access, no patch management, no capacity planning. The trade-off is cold start latency on Lambda, which we've mitigated with provisioned concurrency on the production function. For an academic use case with predictable load patterns, serverless is strictly better than a VPS."

---

## Q9 — "What's the team's go-to-market strategy after ESME?"

**Answer:**
> "Phase 1: ESME as reference customer. One semester of real student usage generates a case study with before/after metrics — cohort risk scores, quiz pass rates, inspector accuracy improvement. Phase 2: use that case study to approach the grandes écoles network. CTOs and deans at CentraleSupélec, Arts et Métiers, and INSA know each other — one warm introduction from ESME faculty gets us in the door. Phase 3: corporate L&D channel. French cybersecurity consulting firms — Wavestone, Synetis, Intrinsec — already sell security awareness programs to their clients. We white-label En Garde and they resell it. We don't need a sales team for phase 3 — we need the right 3 channel partners."

---

## Q10 — "How do you keep the email corpus current with emerging threats?"

**Answer:**
> "Currently: manual curation. We monitor public threat intelligence feeds — PhishTank, OpenPhish, the APWG eCrime reports — and add new EML samples to S3 plus update `answer_key.py`. The admin override table means the ground truth can be updated immediately without a code deploy. On the roadmap: an automated corpus updater that pulls from threat intel APIs and proposes new emails to the admin for review. Amazon Bedrock could assist with automatic signal classification of new samples — reducing curation time from hours to minutes."

---

## Q11 — "What are the biggest security risks in this platform itself?"

**Answer:**
> "Honest answer: three known gaps we've documented. First, the Flask SECRET_KEY is stored as a Lambda environment variable — we've specified moving it to AWS Secrets Manager as a pre-production hardening step. Second, no WAF is deployed on CloudFront — the login endpoint is exposed to credential-stuffing without rate limiting. WAF v2 with managed rule groups is on the critical improvements list. Third, DynamoDB PITR is not yet enabled on all tables — a mistaken batch delete could be irreversible. These are infrastructure configurations, not architectural flaws. They're two Terraform PRs away from being closed."

---

## Q12 — "How do you handle multi-language support for international schools?"

**Answer:**
> "The platform is currently English-only, with French localisation as the first roadmap item. The architecture supports it: all user-facing strings are in Jinja2 templates, not hardcoded in Python. Flask-Babel would handle i18n with minimal route changes. The email corpus itself would need separate French-language samples — phishing emails in French have distinct social engineering patterns from English ones, so it's not a translation task, it's a corpus extension. Realistically, French localisation is a two-month effort post-pilot."

---

## Q13 — "What's the IP/moat — can a larger player copy this in 3 months?"

**Answer:**
> "A larger player could build the UI in 3 months. They cannot build the corpus in 3 months. The 98-email corpus took curation time to classify, write explanations, validate signal accuracy, and test against the scoring engine. More importantly, the moat compounds: every pilot we run generates cohort risk data that tells us which phishing patterns trip students most — informing the next corpus update. The admin-editable answer key architecture is also non-trivial: it requires a DynamoDB override layer that merges with the static key at runtime, not a simple CRUD table. And brand trust in academic networks moves slowly — being first into the grandes écoles network creates switching costs that aren't technical."

---

## Q14 — "What would you do with €50,000 in funding?"

**Answer:**
> "Three buckets. €20k: corpus expansion — source 200 more email samples from licensed threat intelligence providers, run professional red-team review. €15k: AWS WAF, CloudTrail, Config, PITR — closing the production-readiness gaps documented in our AWS improvement report. €15k: go-to-market — pilot onboarding materials, a French-language landing page, a dedicated sales motion targeting 5 grandes écoles. We are not asking for €50k today, but if a jury member writes that check, those are the exact line items."

---

## Q15 — "What metric would tell you this is working?"

**Answer:**
> "One number: the percentage of students who correctly identify a phishing email in the Inspector on their first session versus their third session. If students who complete the full quiz + three inspector sessions are 40% more accurate at signal identification than first-timers — that's working. Secondary: cohort risk score delta. If a class's average risk score drops by 30% after one semester, that's working. We designed those metrics into the data model from day one — the DynamoDB schema captures per-question responses, per-session accuracy, and signal-level hit rates. The analytics are already there. We just need the pilot cohort to generate the data."
