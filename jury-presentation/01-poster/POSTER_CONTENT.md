# A2 Poster Content Brief — En Garde

**Format:** A2 (420 × 594 mm), portrait, PDF export
**Target:** Jury stand — scanned from 1–2 metres; must read at a glance
**Tagline:** *"Turn every student into a phishing detector."*

---

## Layout Grid (6 zones)

```
┌─────────────────────────────────────────────────────────┐
│  HEADER  — ESME logo · En Garde logo · Tagline          │  ~15% height
├──────────────┬──────────────────────┬───────────────────┤
│   PROBLEM    │     SOLUTION          │  ARCHITECTURE     │
│  (left col)  │   (center, widest)    │  (right col)      │  ~45% height
│              │                       │                   │
├──────────────┴──────────────────────┴───────────────────┤
│          KEY METRICS  (4 hero numbers, full width)       │  ~20% height
├─────────────────────────────────────────────────┬───────┤
│  TEAM · ESME · v1.2.3 · March 2026              │  QR   │  ~20% height
└─────────────────────────────────────────────────┴───────┘
```

---

## Zone Content

### HEADER (top 15%)

- **Left:** ESME logo (official SVG/PNG)
- **Center:** "En Garde" in bold display font (suggested: Montserrat ExtraBold 48pt)
- **Tagline below logo:** *"Turn every student into a phishing detector."* (24pt)
- **Right:** v1.2.3 badge + GitHub stars / deployment status icon (optional)

---

### PROBLEM (left column, ~25% width)

**Headline:** The Cost of One Click

**Body copy (3 stat callouts, large numbers):**

> **3.4 billion** phishing emails sent every day *(Statista 2024)*

> **90%** of data breaches start with a phishing email *(IBM X-Force 2024)*

> **€4.5M** average cost of a data breach *(IBM Cost of a Data Breach 2024)*

**Sub-text:**
> Current training is a PDF slideshow employees forget in 72 hours. There is no platform designed for cohort-based engineering schools. We built one.

**Design note:** Use red/orange accent for the numbers. Keep body text at 14–16pt minimum for readability at 2 m.

---

### SOLUTION (center column, ~40% width)

**Headline:** Three Features. One Platform.

**Panel 1 — Quiz System**
- Icon: brain / graduation cap
- Text: *Video-gated training modules. Multiple-choice quizzes with explanations. Rank badges from "Aware" to "Threat Hunter".*

**Panel 2 — Email Inspector**
- Icon: magnifying glass on envelope
- Text: *98 real-world phishing emails. Students classify each email and identify attack signals. Immediate feedback with explanations.*

**Panel 3 — Admin Dashboard**
- Icon: bar chart / shield
- Text: *Cohort risk scores. Answer key editor. CSV user import. No IT department required.*

**Visual:** 3-panel strip with screenshot thumbnails (capture from live app):
- `01-poster/assets/screenshot-quiz-results.png`
- `01-poster/assets/screenshot-inspector-email.png`
- `01-poster/assets/screenshot-admin-dashboard.png`

---

### TECHNICAL ARCHITECTURE (right column, ~25% width)

**Headline:** Serverless. Scalable. GDPR-Native.

**Diagram:** Simplified AWS stack (export/redraw from `documentation/ARCHITECTURE.md`):

```
Browser
  │
  ▼
CloudFront (CDN)
  │
  ├──► API Gateway → Lambda (Flask/Mangum)
  │                    │
  │             ┌──────┴──────┐
  │           DynamoDB       S3
  │           (9 tables)   (EML files)
  │
  └──► S3 (static assets)
```

**3 bullet points below diagram:**
- Scales to 10,000+ students — zero infrastructure management
- ~€0.02 per student per month (AWS pay-per-request)
- Full IaC: Terraform + GitHub Actions OIDC CI/CD

---

### KEY METRICS (bottom band, full width)

4 hero numbers in large tiles:

| | | | |
|---|---|---|---|
| **98** | **10** | **9** | **Serverless** |
| real email samples | attack signal categories | DynamoDB tables | 0 servers managed |

**Design note:** White text on dark background tiles. Numbers at 60–72pt. Labels at 18pt. Equal-width tiles across full poster width.

---

### QR CODE (bottom-right corner, ~10% width)

- QR code linking to live app CloudFront URL **or** GitHub repository
- Label below: *"Try it live"* or *"View on GitHub"*
- Size: minimum 5×5 cm for reliable scanning at 50 cm

---

### FOOTER (bottom strip)

- Team member names (first + last)
- "ESME — Engineering School"
- "March 2026 · v1.2.3"
- Optional: CC BY-NC license icon

---

## Design Guidelines

| Element | Spec |
|---------|------|
| Primary color | Deep navy `#1A2B4A` |
| Accent color | Electric blue `#0066FF` |
| Warning/stat color | Amber `#FF6B2B` |
| Background | White `#FFFFFF` |
| Body font | Inter or Roboto, 14pt minimum |
| Headline font | Montserrat ExtraBold |
| Margins | 20 mm all sides |
| Gutter between columns | 10 mm |

---

## Assets to Capture

Place all screenshots and diagrams in `01-poster/assets/`:

- [ ] `screenshot-quiz-results.png` — quiz results page with rank badge
- [ ] `screenshot-inspector-email.png` — email inspector with parsed email + signals
- [ ] `screenshot-admin-dashboard.png` — admin dashboard risk overview
- [ ] `architecture-simplified.png` — redrawn AWS diagram (simplified for poster)
- [ ] `qr-code.png` — QR code pointing to live URL or repo
