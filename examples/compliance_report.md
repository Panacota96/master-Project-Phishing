# EML Compliance Audit Report

Checks each training EML against its required ANSWER_KEY signals.
**PASS** = signal detected | **WARN** = signal may be missing

| File | Classification | Signal | Status | Detail |
|------|---------------|--------|--------|--------|
| `amazon-web-services-aws-exclusive-100-amazon-gift-card-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `amazon-web-services-aws-urgent-aws-security-update-alert-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `bluejeans-account-verification-request-for-bluejeans-modified.eml` | Phishing | `punycode` | ⚠️ WARN | no xn-- punycode domain found |
| `bluejeans-free-bluejeans-premium-subscription-offer-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `bluejeans-urgent-account-verification-request-modified.eml` | Phishing | `punycode` | ⚠️ WARN | no xn-- punycode domain found |
| `cisco-webex-claim-your-free-webex-pro-offer-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `cisco-webex-urgent-password-reset-required-email-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `display-name-spoof.eml` | Phishing | `impersonation` | ⚠️ WARN | no recognizable brand found in From/Subject/body |
| `fakeinvoice-urgency-spoofing-socialeng.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `google-cloud-platform-gcp-exclusive-rewards-verification-email-modified.eml` | Phishing | `punycode` | ⚠️ WARN | no xn-- punycode domain found |
| `google-cloud-platform-gcp-urgent-account-security-notification-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `google-workspace-exciting-google-workspace-free-upgrade-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `gotomeeting-exclusive-gotomeeting-subscription-upgrade-modified.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `gotomeeting-exclusive-gotomeeting-subscription-upgrade-modified.eml` | Phishing | `punycode` | ⚠️ WARN | no xn-- punycode domain found |
| `gotomeeting-urgent-security-update-for-gotomeeting-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `helpful-neighbor.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `helpful-neighbor.eml` | Phishing | `impersonation` | ⚠️ WARN | no recognizable brand found in From/Subject/body |
| `helpful-neighbor.eml` | Phishing | `urgency` | ⚠️ WARN | no urgency words found |
| `helpful-vendor.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `ibm-cloud-exclusive-ibm-cloud-services-trial-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `ibm-cloud-urgent-account-verification-request-modified.eml` | Phishing | `punycode` | ⚠️ WARN | no xn-- punycode domain found |
| `impersonation-2.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `impersonation-3.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `impersonation-4.eml` | Phishing | `impersonation` | ⚠️ WARN | no recognizable brand found in From/Subject/body |
| `impersonation-4.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `impersonation-attachment-socialeng-spoof.eml` | Phishing | `impersonation` | ⚠️ WARN | no recognizable brand found in From/Subject/body |
| `impersonation-attachment-socialeng-spoof.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `impersonation-socialeng-urgency.eml` | Phishing | `urgency` | ⚠️ WARN | no urgency words found |
| `lateral-phish.eml` | Phishing | `impersonation` | ⚠️ WARN | no recognizable brand found in From/Subject/body |
| `lateral-phish.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `lateral-phish.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `legit-app-2.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `legit-app-4.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `legitapp-impersonation-externaldomain-socialeng.eml` | Phishing | `externaldomain` | ⚠️ WARN | no domain in From header |
| `legitapp-impersonation-externaldomain-socialeng.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `marketing-spam-logistics.eml` | Spam | — | ✅ PASS | Spam – no signals required |
| `microsoft-azure-exclusive-discount-offer-from-microsoft-azure-modified.eml` | Phishing | `punycode` | ⚠️ WARN | no xn-- punycode domain found |
| `microsoft-azure-urgent-account-verification-request-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `microsoft-office-365-exclusive-reward-email-template-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `microsoft-office-365-urgent-account-verification-notice-modified.eml` | Phishing | `punycode` | ⚠️ WARN | no xn-- punycode domain found |
| `microsoft-teams-microsoft-teams-free-upgrade-offer-modified.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `microsoft-teams-microsoft-teams-free-upgrade-offer-modified.eml` | Phishing | `punycode` | ⚠️ WARN | no xn-- punycode domain found |
| `microsoft-teams-urgent-microsoft-teams-account-verification-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `missed-deadline.eml` | Phishing | `fakelogin` | ⚠️ WARN | no fake login indicators found |
| `oracle-cloud-free-oracle-cloud-subscription-offer-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `oracle-cloud-urgent-account-update-request-modified.eml` | Phishing | `punycode` | ⚠️ WARN | no xn-- punycode domain found |
| `phishing-attachment-1.eml` | Phishing | `impersonation` | ⚠️ WARN | no recognizable brand found in From/Subject/body |
| `phishing-attachment-2.eml` | Phishing | `urgency` | ⚠️ WARN | no urgency words found |
| `pixel-tracking.eml` | Phishing | `impersonation` | ⚠️ WARN | no recognizable brand found in From/Subject/body |
| `protected-archive.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `protected-archive.eml` | Phishing | `urgency` | ⚠️ WARN | no urgency words found |
| `punycode-3.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `punycode-4.eml` | Phishing | `fakelogin` | ⚠️ WARN | no fake login indicators found |
| `punycode-impersonation-legitapp-socialeng.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `qr-phishing.eml` | Phishing | `fakelogin` | ⚠️ WARN | no fake login indicators found |
| `realistic-it-reset.eml` | Phishing | `fakelogin` | ⚠️ WARN | no fake login indicators found |
| `realistic-shipping-qr.eml` | Phishing | `urgency` | ⚠️ WARN | no urgency words found |
| `realistic-spam-coupon.eml` | Spam | — | ✅ PASS | Spam – no signals required |
| `realistic-spam-invoice-reminder.eml` | Spam | — | ✅ PASS | Spam – no signals required |
| `realistic-spam-job-offer.eml` | Spam | — | ✅ PASS | Spam – no signals required |
| `realistic-spam-newsletter.eml` | Spam | — | ✅ PASS | Spam – no signals required |
| `realistic-spam-qr.eml` | Spam | — | ✅ PASS | Spam – no signals required |
| `realistic-spam-survey.eml` | Spam | — | ✅ PASS | Spam – no signals required |
| `realistic-spam-unsubscribe-bait.eml` | Spam | — | ✅ PASS | Spam – no signals required |
| `refund-scam.eml` | Phishing | `impersonation` | ⚠️ WARN | no recognizable brand found in From/Subject/body |
| `ringcentral-exclusive-50-discount-offer-modified.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `ringcentral-urgent-account-security-alert-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `skype-for-business-free-year-of-skype-premium-modified.eml` | Phishing | `punycode` | ⚠️ WARN | no xn-- punycode domain found |
| `skype-for-business-urgent-account-verification-request-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `slack-enticing-gift-card-phishing-template-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `slack-urgent-account-security-alert-modified.eml` | Phishing | `punycode` | ⚠️ WARN | no xn-- punycode domain found |
| `spam-2.eml` | Spam | — | ✅ PASS | Spam – no signals required |
| `spam-3.eml` | Spam | — | ✅ PASS | Spam – no signals required |
| `spam-4.eml` | Spam | — | ✅ PASS | Spam – no signals required |
| `spam-attachment-1.eml` | Spam | — | ✅ PASS | Spam – no signals required |
| `spam-attachment-2.eml` | Spam | — | ✅ PASS | Spam – no signals required |
| `sso-spoof.eml` | Phishing | `fakelogin` | ⚠️ WARN | no fake login indicators found |
| `subtle-typo.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `thread-hijacking.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `thread-hijacking.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `urgency-2.eml` | Phishing | `socialeng` | ⚠️ WARN | no social engineering phrases found |
| `urgency-2.eml` | Phishing | `urgency` | ⚠️ WARN | no urgency words found |
| `urgency-4.eml` | Phishing | `fakelogin` | ⚠️ WARN | no fake login indicators found |
| `urgency-4.eml` | Phishing | `impersonation` | ⚠️ WARN | no recognizable brand found in From/Subject/body |
| `zoom-urgent-account-update-required-modified.eml` | Phishing | `spoof` | ⚠️ WARN | no Return-Path header |
| `zoom-zoom-pro-subscription-offer-modified.eml` | Phishing | `punycode` | ⚠️ WARN | no xn-- punycode domain found |

## Summary
- **Total signal checks**: 268
- **Pass**: 195 (72%)
- **Warn**: 73