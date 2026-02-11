# TryHackMe AOC - Email Threat Inspector Answers

## All 6 Emails — Classification, Signals & Flags

| # | Email File | Classification | Signals (select these 3) | Flag |
|---|-----------|---------------|-------------------------|------|
| 1 | `fakeinvoice-urgency-spoofing-socialeng.eml` | **Phishing** | Fake Invoice, Sense of Urgency, Spoofing | `THM{yougotnumber1-keep-it-going}` |
| 2 | `impersonation-attachment-socialeng-spoof.eml` | **Phishing** | Impersonation, Malicious Attachment, Spoofing | `THM{nmumber2-was-not-tha-thard!}` |
| 3 | `impersonation-socialeng-urgency.eml` | **Phishing** | Impersonation, Social Engineering Text, Sense of Urgency | `THM{Impersonation-is-areal-thing-keepIt}` |
| 4 | `legitapp-impersonation-externaldomain-socialeng.eml` | **Phishing** | Impersonation, External Sender Domain, Social Engineering Text | `THM{Get-back-SOC-mas!!}` |
| 5 | `marketing-spam-logistics.eml` | **Spam** | *(none — just select Spam)* | `THM{It-was-just-a-sp4m!!}` |
| 6 | `punycode-impersonation-legitapp-socialeng.eml` | **Phishing** | Typosquatting/Punycodes, Impersonation, Social Engineering Text | `THM{number6-is-the-last-one!-DX!}` |

---

## Quick Reference — Signal Aliases

| Signal Label | Alias |
|-------------|-------|
| Impersonation | impersonation |
| Typosquatting/Punycodes | punycode |
| External Sender Domain | externaldomain |
| Spoofing | spoof |
| Social Engineering Text | socialeng |
| Sense of Urgency | urgency |
| Fake Invoice | fakeinvoice |
| Malicious Attachment | attachment |
| Fake Login Page | fakelogin |
| Side Channel Communication Attempt | sidechannel |
