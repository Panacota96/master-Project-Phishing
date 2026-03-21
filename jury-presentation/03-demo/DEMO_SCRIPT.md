# Live Demo Script — En Garde

**Total time:** 5–6 minutes
**Goal:** Show both student and admin experiences end-to-end
**Presenter:** Person A (student flow) + Person B (admin flow)

---

## Pre-Demo Setup

Before the jury enters the room:
- Browser Tab 1: student account logged in, quiz list page visible
- Browser Tab 2: admin account logged in, dashboard page visible
- Inspector pool pre-loaded (navigate to `/inspector` in student tab)
- Screen mirrored to projector; resolution confirmed

---

## ACT 1 — Student Experience (~3 minutes)

### Step 1 — Login & Quiz List (20 sec)
- Show the student login page (pre-filled or already logged in)
- Navigate to the quiz list
- Point out: *"A student can see which quizzes are available and which badges they've earned."*

### Step 2 — Video Gate (20 sec)
- Click "Phishing Awareness Fundamentals"
- Show the video gate page: *"Training video must complete before the quiz unlocks. You can't skip the learning."*
- Click "I've watched the video" (or skip button if enabled in test env)

### Step 3 — Take a Quiz Question (30 sec)
- Show the quiz question view
- Deliberately select a **wrong answer**
- Submit → show the immediate explanation: *"Even a wrong answer teaches something. The explanation shows exactly why that option was incorrect."*
- Navigate to the next question, select the correct answer

### Step 4 — Results & Badge (20 sec)
- Complete the quiz (or fast-forward to results if demo account has saved progress)
- Show results page with score and rank badge (e.g., "Threat Hunter")
- *"Students see their rank immediately. Gamification drives re-engagement."*

### Step 5 — Email Inspector Pool (20 sec)
- Click "Email Threat Inspector" in the nav
- Show the pool of 8 emails: *"Each session gets a unique mix of phishing and spam emails drawn from our 98-email corpus."*
- Point to the session counter

### Step 6 — Analyze One Email (50 sec)
- Click on an email (choose the Amazon AWS impersonation one for visual impact)
- Walk through tabs:
  - **Headers tab**: show spoofed From address
  - **HTML preview tab**: show the polished phishing template
  - **Links tab**: show the suspicious external domain
- *"Students see the raw anatomy of a phishing email — the same view a security analyst has."*

### Step 7 — Classify & Submit (30 sec)
- Select classification: **Phishing**
- Check 3 signal checkboxes: `impersonation`, `urgency`, `externaldomain`
- Click Submit
- Show the feedback: correct signals in green, any missed signals in red with explanation
- *"Immediate scored feedback. This is how muscle memory forms."*

---

## ACT 2 — Admin Power (~2 minutes)

### Step 8 — Switch to Admin Tab (5 sec)
- Switch to Browser Tab 2 (admin already logged in)
- *"Now let me show you what the professor sees."*

### Step 9 — Dashboard Overview (30 sec)
- Show the admin dashboard: quiz completion stats, recent activity
- Point to cohort risk scores (color-coded red/amber/green by class)
- *"At a glance, the professor sees which cohorts are most vulnerable. Red means they need re-training."*

### Step 10 — Answer Key Editor (40 sec)
- Navigate to the Answer Key section
- Click "Edit" on one email entry (e.g., change a signal)
- Show the override form
- Save → show "overridden" badge on the entry
- *"When a new phishing campaign emerges, the professor updates the answer key here. No code deployment. No IT ticket. Thirty seconds."*

### Step 11 — User Management (20 sec)
- Navigate to Users
- Show the CSV import button
- *"Onboarding 200 students takes two minutes — upload a CSV, done."*

---

## Closing Hook (15 sec)

> *[Return to student results page]*
>
> "In 5 minutes, this student went from zero knowledge to correctly identifying the signals in a real Amazon phishing campaign. Imagine 500 students doing this before their first internship. That is En Garde."

---

## Demo Tips

- Move the mouse **slowly and deliberately** — juries follow the cursor
- Narrate what you are about to click, then click it
- If a page loads slowly, fill the silence with context: *"This is a cold Lambda start — in production with provisioned concurrency, this loads instantly"*
- If anything breaks → smile, switch to the backup tab with screenshots, continue narrating
