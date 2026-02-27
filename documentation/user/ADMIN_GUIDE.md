# Administrator User Guide — Phishing Awareness Training

## Overview

As an administrator you can manage users, import cohorts, view platform-wide analytics, manage the Email Threat Inspector answer key, and triage bug reports.

> **Accounts are admin-created.** There is no self-registration — students cannot sign up on their own. Create accounts individually or via CSV bulk import before the course starts.

---
> **📸 Screenshot placeholder**
> *Insert screenshot of the Admin dashboard overview (stats cards + charts) here*

---

## 👤 1. User and Cohort Management

Managing users by cohort is key to tracking progress across different groups.

### 1.1 View Users

Go to **Admin → Users** to see the full list of registered users with their cohort metadata and roles.

---
> **📸 Screenshot placeholder**
> *Insert screenshot of the User list page here*

---

### 1.2 Cohort Fields

Each user belongs to a cohort defined by:

| Field | Example |
|-------|---------|
| **Class Name** | `Class A` |
| **Academic Year** | `2025` |
| **Major** | `CS`, `Engineering` |
| **Facility** | `Paris`, `Lyon` |
| **Group** | `default`, `lab-1` |

### 1.3 Import Users via CSV

For large cohorts use the bulk import feature.

**CSV column order:**
```
username,email,password,class_name,academic_year,major,facility,group
```

- `facility` is **mandatory**.
- `group` defaults to `default` if omitted.

**Example row:**
```
alice,alice@example.com,TempPass1!,Class A,2025,CS,Paris,lab-1
```

**Steps:**
1. Go to **Admin → Import Users**.
2. Choose your CSV file.
3. Click **Import**.

---
> **📸 Screenshot placeholder**
> *Insert screenshot of the CSV import page (file picker + import button) here*

---

### 1.4 Reset Password

Find the user in the **Users** list and click **Reset Password**.

### 1.5 Delete Inactive Accounts

On **Admin → Manage Users**, locate the account and click **Delete**.

---

## 📊 2. Analytics and Reporting

Gain insights into user performance and training effectiveness.

### 2.1 Global Stats

The main dashboard shows total users, total attempts, and average scores at a glance.

### 2.2 Score Distribution

The **Score Distribution** bar chart (Chart.js) shows how scores spread across the student population.

---
> **📸 Screenshot placeholder**
> *Insert screenshot of the Score distribution chart here*

---

### 2.3 Signal Accuracy

The **Signal Accuracy Polar Chart** identifies which phishing signals (e.g., Punycode, Spoofing) students are most often missing. Use this to prioritise future training videos.

### 2.4 Human Risk Analysis

Click **View Human Risk Analysis** to see the **Vulnerability Index**:

- **Risk Scoring**: visualises which cohorts (Class / Year / Major) are most susceptible based on simulation failure rates.
- **Colour Coding**: high-risk groups flagged in Red, moderate in Yellow, low-risk in Green.

---
> **📸 Screenshot placeholder**
> *Insert screenshot of the Cohort analytics / risk analysis page here*

---

### 2.5 Quiz Analytics

Each quiz has its own stats page: number of attempts, average score, and per-question breakdown.

### 2.6 Cohort Reports

Filter by class, academic year, or major to compare performance across cohorts.

### 2.7 Download Reports

| Report | Location |
|--------|----------|
| Quiz attempts & scores | **Admin → Analytics → Download CSV** |
| Inspector classifications | **Admin → Inspector Analytics → Download CSV** |

---

## 🔍 3. Inspector Analytics

Monitor how students classify and identify phishing signals in real-world emails.

### 3.1 Overview

Go to **Admin → Inspector Analytics** to see the total number of classification attempts and the signal distribution.

---
> **📸 Screenshot placeholder**
> *Insert screenshot of the Inspector analytics overview page here*

---

### 3.2 Answer Key Editor

Click **View Answer Key & Troubleshoot** to open the answer key table.

- **Reference view**: shows the correct classification (Spam / Phishing) and required signals for every email file. Signal count is **dynamic per email** — it is not fixed at 3.
- **Edit overrides**: click **Edit** on any row to change the classification or required signals. Changes are saved to `DYNAMODB_ANSWER_KEY_OVERRIDES` and take effect immediately. Overridden rows are marked with a yellow **"overridden"** badge.
- **Reset to Default**: click to remove the override and revert to the static answer key for that email.

---
> **📸 Screenshot placeholder**
> *Insert screenshot of the Answer key editor (with an overridden row highlighted) here*

---

### 3.3 Live Email Preview

From the answer key table, click **Preview** on any row to open a modal showing exactly how the Inspector parses and cleans (removes template placeholders from) that email — the same view students see.

---
> **📸 Screenshot placeholder**
> *Insert screenshot of the Email live preview modal here*

---

### 3.4 Reset Inspector Access

If a student needs to redo their Inspector session, find them on the **Admin → Users** page and click **Reset Inspector Access**. This unlocks all 8 emails for re-submission.

---
> **📸 Screenshot placeholder**
> *Insert screenshot of the Reset inspector access button/confirmation here*

---

## 🐛 4. Bug Report Management

Monitor student feedback and system issues.

1. Go to **Admin → Bug Reports** to see all submitted issues.
2. Each report includes the student's username and the exact page URL where the issue occurred.
3. Use the **Status** dropdown to mark reports as **Open** or **Fixed**.

---
> **📸 Screenshot placeholder**
> *Insert screenshot of the Bug report list page here*

---
