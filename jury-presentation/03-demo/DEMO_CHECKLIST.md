# Pre-Demo Checklist — En Garde

Complete these steps **the day before** AND **30 minutes before** the jury presentation.

---

## Day Before — Infrastructure

- [ ] Confirm AWS dev environment is deployed and healthy
  - Run: `curl -I https://<CLOUDFRONT_DOMAIN>/health` → expect `200 OK`
  - Check CloudWatch dashboard for any recent Lambda errors or alarms
- [ ] Verify CloudFront URL is accessible (not blocked by ESME campus network or room WiFi)
  - Test from a phone on cellular and from the presentation room's WiFi
- [ ] Confirm API Gateway stage is deployed and not throttled
- [ ] Check S3 bucket contains EML samples (`eml-samples/` prefix has files)
- [ ] Verify SES identity is verified if QR registration demo is included

## Day Before — Test Data

- [ ] Seed a fresh student test account (username: `demo-student`, password: known)
  - Run: `python seed_dynamodb.py` or create manually via admin UI
  - Verify student can log in and sees quiz list
  - Verify student has NOT taken any quiz yet (clean state for demo)
- [ ] Confirm admin account exists and dashboard loads (username: `demo-admin`)
- [ ] Pre-load Inspector pool for demo-student: navigate to `/inspector`, confirm 8 emails load
- [ ] Test email detail for the Amazon AWS impersonation email — confirm headers, HTML preview, and links tabs render correctly
- [ ] Test one full submit flow: classify + signals → confirm feedback renders

## Day Before — Slides & Fallback

- [ ] Slide deck exported as PDF (Google Slides → File → Download as PDF)
- [ ] PDF saved on USB stick AND emailed to self
- [ ] 8 demo screenshots captured (all steps in DEMO_SCRIPT.md) and saved in `03-demo/assets/`
- [ ] Pre-recorded demo video (MP4, ~3 min, subtitled) saved in `03-demo/assets/` and on USB
- [ ] Backup laptop tested with screenshots opened and ready

## 30 Minutes Before — Final Checks

- [ ] Laptop charged + charger in bag
- [ ] HDMI adapter (or USB-C to HDMI) in bag
- [ ] Phone as WiFi hotspot configured (test it works)
- [ ] Poster printed at A2, rolled and protected
- [ ] Browser pre-loaded:
  - Tab 1: Student session — quiz list page visible, logged in as `demo-student`
  - Tab 2: Admin session — dashboard page visible, logged in as `demo-admin`
  - Tab 3: Inspector page (student) — email pool loaded, first email detail open
  - Tab 4: Fallback screenshots folder (local file)
- [ ] Presenter notes printed (one copy each)
- [ ] Timer app ready on phone (10-minute countdown)
- [ ] Ask the room: "Is there a screen? What's the input? Is there WiFi?" — test connection before jury enters

---

## Quick-Fix Reference

| Problem | Fix |
|---------|-----|
| Page loads slowly | Lambda cold start — wait 3 sec, narrate while waiting |
| Inspector email pool empty | Check S3 has EML files; or use a pre-seeded demo account |
| Admin dashboard blank | Check DynamoDB DYNAMODB_ATTEMPTS table has entries; seed with `seed_dynamodb.py` |
| CloudFront 403 | Check S3 bucket policy and OAC; or switch to local screenshots |
| No WiFi in room | Use phone hotspot; or switch entirely to pre-recorded video |
