# Fallback Plan — En Garde Demo

**Trigger:** Use this plan if live demo fails (no network, AWS cold start loop, browser crash, etc.)

**Rule:** Never apologize for a failed demo. Transition smoothly: *"Let me show you the recorded walkthrough while I reset the environment."* Then never return to the live demo — stay on fallback.

---

## Fallback Option A — Pre-Recorded Video (preferred)

**File:** `03-demo/assets/demo-video.mp4`
**Duration:** ~3 minutes
**Subtitled:** Yes (English)

**How to use:**
1. Open VLC or the default video player (have it pre-loaded in a browser tab or desktop)
2. Say: *"Let me show you a quick walkthrough of the platform."*
3. Play the video — narrate live over the subtitles to add energy
4. Pause at key moments (quiz results badge, inspector feedback, admin answer key editor) to make a verbal point

**Video must cover:**
- Student login → quiz list
- Video gate → quiz question with wrong answer + explanation
- Results page with rank badge
- Inspector pool → email detail (headers, HTML preview, links)
- Classify + signal selection → feedback screen
- Admin dashboard → cohort risk scores
- Answer key editor → override saved

---

## Fallback Option B — Annotated Screenshots

**Files:** `03-demo/assets/screenshots/`

| Filename | Step |
|----------|------|
| `01-login-quiz-list.png` | Student login and quiz list |
| `02-video-gate.png` | Video gate page |
| `03-quiz-question.png` | Quiz question with answer options |
| `04-quiz-explanation.png` | Wrong answer explanation screen |
| `05-results-badge.png` | Results page with rank badge |
| `06-inspector-pool.png` | Inspector email pool (8 emails) |
| `07-inspector-email-headers.png` | Email detail — headers tab |
| `08-inspector-email-preview.png` | Email detail — HTML preview tab |
| `09-inspector-signals.png` | Signal selection UI |
| `10-inspector-feedback.png` | Submit feedback (correct/incorrect signals) |
| `11-admin-dashboard.png` | Admin dashboard overview |
| `12-admin-risk-scores.png` | Cohort risk scores (color-coded) |
| `13-admin-answer-key.png` | Answer key editor |

**How to use:**
1. Open a local folder in Windows Explorer or a browser tab
2. Click through screenshots while narrating from DEMO_SCRIPT.md
3. Say: *"The live environment is recovering — let me walk you through the key screens."*

---

## Fallback Option C — Architecture Walk

**Use when:** No video, no screenshots, projector not working (rare)

Walk through `documentation/ARCHITECTURE.md` on the projector or laptop screen:

1. **System Overview diagram** — explain the actors (student, professor, admin) and how they interact with the system
2. **Quiz Flow diagram** — show the video gate + one-attempt enforcement logic
3. **Email Inspector Flow diagram** — show the S3 → Lambda → DynamoDB → anonymous storage chain
4. **CI/CD Pipeline diagram** — show the GitHub Actions → Terraform → AWS deploy chain

Narrate each diagram for 30–45 seconds. This demonstrates technical depth even without a running app.

---

## What to Say When Switching to Fallback

| Situation | Line |
|-----------|------|
| Network down | *"The campus network seems to be blocking CloudFront — let me show you the recorded walkthrough instead."* |
| Lambda timeout | *"We're on a Lambda cold start — while that resolves, let me walk you through the key screens."* |
| Browser crash | *"No problem — I have a backup ready."* (open screenshots immediately, no further explanation) |

**Never say:**
- "I'm sorry"
- "This is embarrassing"
- "It usually works"
- "I don't know what happened"

**The fallback is not failure — it is preparation. Preparation is a feature.**
