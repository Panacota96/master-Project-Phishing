# Student User Guide — Phishing Awareness Training

## Introduction

The Phishing Awareness Training Application helps you recognise and defend against phishing attacks through two complementary activities: knowledge quizzes and a hands-on Email Threat Inspector.

> **Note:** There is no self-registration. Your account is created by your instructor before the course starts. You will receive your username and a temporary password by email or in class.

---

## Student Learning Path

```mermaid
flowchart TD
    A[Receive credentials from admin] --> B[Login to App]
    B --> C[Change password on first login]
    C --> D{Choose Activity}
    D -- "Quiz" --> E[Watch Training Video]
    E --> F[Take Multiple-Choice Quiz]
    F --> G[Review Feedback & Score]
    D -- "Threat Inspector" --> H[Select Assigned Email]
    H --> I[Analyze Headers & Links]
    I --> J[Submit Classification & Signals]
    J --> K[Lock/Complete Attempt]
```

---

## 1. Getting Started

### 1.1 Login

1. Open the training URL in your browser.
2. Enter the **username** and **password** provided by your instructor.
3. Click **Login**.

You are taken to your personal dashboard showing available quizzes and your progress.

### 1.2 Change Your Password (Recommended on First Login)

Your instructor created your account with a temporary password. You should change it immediately.

1. After logging in, click your username in the top-right corner and select **Change Password** (or navigate to **Settings → Change Password**).
2. Enter your current (temporary) password.
3. Enter and confirm your new password.
4. Click **Save**.

### 1.3 Dashboard

After logging in you land on your personal dashboard, which shows:
- Quizzes available and your progress
- Your current rank badge
- A link to the Email Threat Inspector

---

## 2. Phishing Quizzes

Quizzes test your knowledge of phishing techniques such as URL analysis, spoofing, and urgency tactics.

### 2.1 Select a Quiz

1. From the dashboard (or **My Quizzes** in the sidebar), browse the list of available quizzes.
2. Each quiz card shows its title, description, and whether you have already completed it.
3. Click the quiz you want to take.

### 2.2 Watch the Training Video

Each quiz is gated behind a short training video that introduces the topic. You must watch it before the quiz unlocks.

1. Click **Watch Video**.
2. Watch the full video — the **Start Quiz** button activates once you reach the end.

### 2.3 Take the Quiz

1. Click **Start Quiz** after the video.
2. Answer each multiple-choice question and confirm your choice.
3. You receive immediate per-question feedback with an explanation of the correct answer.

### 2.4 Quiz Completion and Results

After the last question you see your results page showing:
- Your **score** and **percentage**
- A **rank badge** based on your performance (see §5 for rank criteria)
- A breakdown of which questions you answered correctly

Your progress is saved permanently — the quiz shows as completed in your quiz list. Visit **My Quizzes** to see your full history and scores.

> You may only attempt each quiz **once**.

---

## 3. Email Threat Inspector

The Email Threat Inspector lets you analyse real-world phishing and spam emails in a safe, sandboxed environment.

### 3.1 Open the Inspector

Click **Email Threat Inspector** in the sidebar.

You are assigned a personal pool of up to **8 emails** (a mix of spam and phishing samples). The sidebar lists your assigned emails with their subject, sender, and date.

### 3.2 Analyse an Email

Click on an email in your list to open the analysis view. Use the tabs to examine the email from different angles:

| Tab | What to look for |
|-----|-----------------|
| **Overview** | Sender, recipient, subject, date |
| **Headers** | `Return-Path`, `Reply-To`, SPF/DKIM/DMARC results |
| **HTML Preview** | How the email looks in an inbox (safely sandboxed) |
| **Links** | Extracted URLs — look for look-alike or punycode domains |
| **Attachments** | Filename, size, MIME type — flag dangerous types (`.exe`, `.zip`, `.html`) or double extensions (`.pdf.exe`) |

### 3.3 Classify the Threat and Identify Signals

1. At the bottom of the analysis view, select the **classification**: **Phishing** or **Spam**.
2. If you selected **Phishing**, tick all the **signals** you identified (see §4 for the full list). The number of required signals varies per email.
3. Click **Submit**.

> Each email can only be submitted **once** — your answer is final.

### 3.4 Inspector Completion

Once you have submitted all 8 emails, the Inspector session is locked and you see a completion screen confirming all your submissions are recorded. Your results are saved anonymously for analysis by your instructor.

If you need to redo your session, contact your instructor — admins can reset inspector access for individual students.

---

## 4. Phishing Signals to Watch For

| Signal | Description |
|--------|-------------|
| **Impersonation** | Pretending to be a trusted person or brand |
| **Urgency** | Creating fear or time pressure to provoke hasty action |
| **Typosquatting / Punycode** | Using look-alike or unicode domains (e.g. `paypaI.com`) |
| **Spoofing** | Faking the `From` address |
| **Social Engineering** | Manipulating you into revealing sensitive information |
| **External Domain** | Links pointing to a domain unrelated to the claimed sender |
| **Fake Invoice / Fake Login** | Fraudulent documents or credential-harvesting pages |
| **Attachment** | Dangerous file attachment |
| **Side Channel** | Redirecting communication off the main platform (WhatsApp, SMS) |

---

## 5. Training Journey & Ranks

Track your progress and earn ranks as you complete quizzes:

| Rank | Criteria |
|------|----------|
| **Novice** | Just starting out |
| **Trainee** | Making progress |
| **Defender** | Consistently identifying threats |
| **Cyber Sentinel** | 90%+ average score — mastery of phishing awareness |

The progress bar on your dashboard shows how many of the available quizzes you have completed. Your rank badge updates automatically as you improve.

---

## 6. Reporting Bugs

If you encounter a technical issue:

1. Click **Report Bug** in the top navigation bar (next to Logout).
2. Describe what went wrong.
3. Click **Submit** — your username and the current page URL are attached automatically to help the admin troubleshoot.
