# Business Model — En Garde

**Model type:** SaaS (Software-as-a-Service), annual subscription
**Billing unit:** Per-student per month
**Primary buyer:** Institution (school, company L&D department) — not individual students

---

## Pricing Tiers

| Tier | Price | User Cap | Features | Target Customer |
|------|-------|----------|----------|----------------|
| **Starter** | €2/student/month | 50 users | Quiz system + Email Inspector, basic reporting | Individual professors, bootcamps, pilot deployments |
| **Pro** | €5/student/month | 500 users | + Admin dashboard, cohort risk scores, CSV bulk import, answer key editor, CloudWatch monitoring | Engineering schools, IUTs, BTS programs |
| **Enterprise** | Custom (~€3–4k/year flat) | Unlimited | + Custom email corpus, API access, dedicated SLA, SSO/SAML, multi-institution admin, white-label | Grandes écoles, corporate L&D, government agencies |

---

## Unit Economics — Pro Tier (200-Student School)

| Line item | Monthly | Annual |
|-----------|---------|--------|
| **Revenue** | €1,000 | €12,000 |
| AWS Lambda (invocations + GB-seconds) | ~€8 | ~€96 |
| AWS DynamoDB (pay-per-request) | ~€10 | ~€120 |
| AWS S3 (storage + GET requests for EML) | ~€3 | ~€36 |
| AWS CloudFront (data transfer) | ~€5 | ~€60 |
| AWS SES (email notifications) | ~€2 | ~€24 |
| AWS SQS (registration worker) | ~€1 | ~€12 |
| **Total AWS COGS** | **~€29** | **~€348** |
| **Gross Profit** | **~€971** | **~€11,652** |
| **Gross Margin** | **~97%** | **~97%** |

*Note: Excludes personnel costs, customer acquisition cost, and overhead.*

---

## Unit Economics — Starter Tier (30 Users)

| Line item | Monthly | Annual |
|-----------|---------|--------|
| Revenue | €60 | €720 |
| AWS COGS (estimated) | ~€5 | ~€60 |
| Gross Profit | ~€55 | ~€660 |
| Gross Margin | ~92% | ~92% |

*Starter tier is intentionally low-margin as a pilot/land-and-expand vehicle, not the primary revenue driver.*

---

## Revenue Model Summary

**Year 1 target (conservative):**
- 5 Pro schools × €12,000/year = €60,000
- 10 Starter pilots × €720/year = €7,200
- 1 Enterprise deal × €4,000/year = €4,000
- **Total ARR: ~€71,200**

**Year 2 target (expansion + churn model):**
- Net Revenue Retention target: 120% (upsell Starter → Pro, add new schools)
- Churn target: < 5% annually (institutional contracts are sticky)

---

## Go-to-Market Strategy

### Phase 1 — Reference Customer (Months 1–6)
- ESME as founding pilot: free access, direct feedback, joint case study
- Metric: cohort risk score improvement over one semester
- Output: 1-page case study with before/after data → used in all subsequent sales

### Phase 2 — Grandes Écoles Expansion (Months 6–18)
- Use ESME faculty network for warm introductions
- Target: CentraleSupélec, Arts et Métiers ENSAM, INSA Lyon, ISEP
- Sales motion: 30-minute demo + 1-semester Starter pilot → convert to Pro at renewal
- Expected close rate: 30% of demos to paid (academic sales cycle: 3–4 months)

### Phase 3 — Corporate L&D Channel (Months 12–24)
- Partner with French cybersecurity consulting firms (Wavestone, Synetis, Intrinsec)
- White-label En Garde as part of their security awareness offering
- Revenue share: 20% to partner, 80% to En Garde
- Advantage: partners bring existing enterprise relationships; we bring the platform

---

## Cost Structure (Operating Model, Year 1)

| Cost | Type | Estimate |
|------|------|---------|
| AWS infrastructure (all tiers) | Variable | ~€2,000/year |
| Domain + SSL + SES sending | Fixed | ~€200/year |
| GitHub Actions minutes | Fixed | Free tier (public repo) |
| Legal (DPA templates, T&C) | One-time | ~€1,500 |
| Marketing (landing page, deck) | One-time | ~€500 |
| **Total Year 1 cash costs** | | **~€4,200** |

*Team compensation excluded — academic project context. Pre-revenue operating costs are minimal due to serverless architecture.*

---

## Financial Projections (3-Year)

| Year | ARR | Schools (Pro) | Gross Margin |
|------|-----|--------------|-------------|
| 2026 | €71k | 5 | ~95% |
| 2027 | €240k | 15 | ~95% |
| 2028 | €600k | 35 + 2 Enterprise | ~94% |

*Break-even on cash costs achieved in Month 2 of first paying Pro customer.*

---

## Key Metrics to Track

| Metric | Target | Why |
|--------|--------|-----|
| ARR | €71k (Year 1) | Primary revenue KPI |
| Net Revenue Retention | >120% | Measures product stickiness + upsell |
| CAC (Cost to Acquire Customer) | <€500 | Low-touch sales motion |
| LTV (Pro school, 3 years) | ~€36k | Institutional switching costs are high |
| LTV:CAC ratio | >72x | Exceptional for SaaS |
| Churn rate | <5% annually | Academic contracts renew with academic year |
| Cohort risk score improvement | >30% per semester | Core product efficacy metric |
