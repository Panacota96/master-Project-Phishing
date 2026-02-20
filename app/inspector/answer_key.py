ANSWER_KEY = {
    # ─── 1. FAKE INVOICE ──────────────────────────────────────────────────────
    "fakeinvoice-urgency-spoofing-socialeng.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "urgency", "spoof"],
    },
    "invoice-2.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "urgency", "spoof"],
    },
    "invoice-3.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "externaldomain", "impersonation"],
    },
    "invoice-4.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "fakeinvoice", "externaldomain"],
    },

    # ─── 2. IMPERSONATION ─────────────────────────────────────────────────────
    "impersonation-attachment-socialeng-spoof.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "attachment", "spoof"],
    },
    "impersonation-2.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "externaldomain", "socialeng"],
    },
    "impersonation-3.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "externaldomain"],
    },
    "impersonation-4.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "spoof"],
    },

    # ─── 3. IMPERSONATION URGENCY ─────────────────────────────────────────────
    "impersonation-socialeng-urgency.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "urgency"],
    },
    "urgency-2.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "urgency"],
    },
    "urgency-3.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
    },
    "urgency-4.eml": {
        "classification": "Phishing",
        "signals": ["urgency", "fakelogin", "impersonation"],
    },

    # ─── 4. LEGIT APP IMPERSONATION ───────────────────────────────────────────
    "legitapp-impersonation-externaldomain-socialeng.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "externaldomain", "socialeng"],
    },
    "legit-app-2.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "externaldomain"],
    },
    "legit-app-3.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
    },
    "legit-app-4.eml": {
        "classification": "Phishing",
        "signals": ["attachment", "socialeng", "spoof"],
    },

    # ─── 5. PUNYCODE ──────────────────────────────────────────────────────────
    "punycode-impersonation-legitapp-socialeng.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "impersonation", "socialeng"],
    },
    "punycode-2.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "impersonation", "externaldomain"],
    },
    "punycode-3.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "urgency", "spoof"],
    },
    "punycode-4.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "fakelogin", "externaldomain"],
    },

    # ─── 6. SPAM ──────────────────────────────────────────────────────────────
    "marketing-spam-logistics.eml": {
        "classification": "Spam",
        "signals": [],
    },
    "spam-2.eml": {
        "classification": "Spam",
        "signals": [],
    },
    "spam-3.eml": {
        "classification": "Spam",
        "signals": [],
    },
    "spam-4.eml": {
        "classification": "Spam",
        "signals": [],
    },
    "phishing-attachment-1.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "attachment", "urgency"],
    },
    "phishing-attachment-2.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "attachment", "urgency"],
    },
    "spam-attachment-1.eml": {
        "classification": "Spam",
        "signals": [],
    },
    "spam-attachment-2.eml": {
        "classification": "Spam",
        "signals": [],
    },
    "realistic-spam-coupon.eml": {
        "classification": "Spam",
        "signals": [],
    },
    "realistic-spam-newsletter.eml": {
        "classification": "Spam",
        "signals": [],
    },
    "realistic-spam-qr.eml": {
        "classification": "Spam",
        "signals": [],
    },
    "realistic-spam-survey.eml": {
        "classification": "Spam",
        "signals": [],
    },
    "realistic-spam-job-offer.eml": {
        "classification": "Spam",
        "signals": [],
    },
    "realistic-spam-unsubscribe-bait.eml": {
        "classification": "Spam",
        "signals": [],
    },
    "realistic-spam-invoice-reminder.eml": {
        "classification": "Spam",
        "signals": [],
    },
    "realistic-invoice-qr.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "urgency", "externaldomain"],
    },
    "realistic-it-reset.eml": {
        "classification": "Phishing",
        "signals": ["fakelogin", "urgency", "externaldomain"],
    },
    "realistic-shipping-qr.eml": {
        "classification": "Phishing",
        "signals": ["externaldomain", "socialeng", "urgency"],
    },
    "pixel-tracking.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "sidechannel"],
    },
    "thread-hijacking.eml": {
        "classification": "Phishing",
        "signals": ["urgency", "socialeng", "spoof"],
    },
    "subtle-typo.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "urgency", "spoof"],
    },
    "homograph-attack.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "impersonation", "urgency"],
    },
    "qr-phishing.eml": {
        "classification": "Phishing",
        "signals": ["fakelogin", "impersonation", "socialeng"],
    },
    "lateral-phish.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "spoof"],
    },
    "subdomain-deception.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "impersonation", "fakelogin"],
    },
    "helpful-vendor.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "externaldomain", "socialeng"],
    },
    "display-name-spoof.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "spoof", "urgency"],
    },
    "helpful-neighbor.eml": {
        "classification": "Phishing",
        "signals": ["socialeng", "impersonation", "urgency"],
    },
    "missed-deadline.eml": {
        "classification": "Phishing",
        "signals": ["urgency", "socialeng", "fakelogin"],
    },
    "refund-scam.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "socialeng", "impersonation"],
    },
    "protected-archive.eml": {
        "classification": "Phishing",
        "signals": ["attachment", "socialeng", "urgency"],
    },
    "sso-spoof.eml": {
        "classification": "Phishing",
        "signals": ["fakelogin", "impersonation", "externaldomain"],
    },
    "callback-phish.eml": {
        "classification": "Phishing",
        "signals": ["sidechannel", "socialeng", "urgency"],
    },
    # ─── LINKSEC TEMPLATES ─────────────────────────────────────────────
    "amazon-web-services-aws-aws-account-verification-request-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
    },
    "amazon-web-services-aws-exclusive-100-amazon-gift-card-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "spoof"],
    },
    "amazon-web-services-aws-urgent-aws-security-update-alert-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "spoof"],
    },
    "bluejeans-account-verification-request-for-bluejeans-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "punycode"],
    },
    "bluejeans-exclusive-upgrade-offer-template-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "externaldomain"],
    },
    "bluejeans-free-bluejeans-premium-subscription-offer-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "spoof"],
    },
    "bluejeans-profile-viewing-notification-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "externaldomain"],
    },
    "bluejeans-urgent-account-verification-request-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "punycode"],
    },
    "cisco-webex-claim-your-free-webex-pro-offer-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "spoof"],
    },
    "cisco-webex-urgent-password-reset-required-email-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "spoof"],
    },
    "cisco-webex-urgent-webex-account-verification-request-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
    },
    "google-cloud-platform-gcp-exclusive-rewards-verification-email-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "punycode"],
    },
    "google-cloud-platform-gcp-urgent-account-security-notification-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "spoof"],
    },
    "google-cloud-platform-gcp-urgent-gcp-service-alert-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
    },
    "google-workspace-exciting-google-workspace-free-upgrade-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "spoof"],
    },
    "google-workspace-urgent-google-workspace-account-verification-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "externaldomain"],
    },
    "google-workspace-urgent-google-workspace-storage-alert-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
    },
    "gotomeeting-exclusive-gotomeeting-subscription-upgrade-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "punycode"],
    },
    "gotomeeting-urgent-account-verification-request-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
    },
    "gotomeeting-urgent-security-update-for-gotomeeting-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "spoof"],
    },
    "ibm-cloud-exclusive-ibm-cloud-services-trial-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "spoof"],
    },
    "ibm-cloud-urgent-account-verification-request-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "punycode"],
    },
    "ibm-cloud-urgent-security-update-notification-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
    },
    "microsoft-azure-exclusive-discount-offer-from-microsoft-azure-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "punycode"],
    },
    "microsoft-azure-new-security-features-alert-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "externaldomain"],
    },
    "microsoft-azure-urgent-account-verification-request-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "spoof"],
    },
    "microsoft-office-365-exclusive-reward-email-template-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "spoof"],
    },
    "microsoft-office-365-urgent-account-verification-notice-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "punycode"],
    },
    "microsoft-teams-exclusive-microsoft-365-upgrade-offer-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "externaldomain"],
    },
    "microsoft-teams-microsoft-teams-free-upgrade-offer-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "punycode"],
    },
    "microsoft-teams-urgent-microsoft-teams-account-verification-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "spoof"],
    },
    "oracle-cloud-free-oracle-cloud-subscription-offer-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "spoof"],
    },
    "oracle-cloud-urgent-account-update-request-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "punycode"],
    },
    "ringcentral-exclusive-50-discount-offer-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "externaldomain"],
    },
    "ringcentral-urgent-account-security-alert-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "spoof"],
    },
    "ringcentral-urgent-subscription-renewal-notice-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
    },
    "skype-for-business-free-year-of-skype-premium-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "punycode"],
    },
    "skype-for-business-urgent-account-verification-request-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "spoof"],
    },
    "skype-for-business-urgent-password-reset-reminder-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
    },
    "slack-enticing-gift-card-phishing-template-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "spoof"],
    },
    "slack-urgent-account-security-alert-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "punycode"],
    },
    "slack-urgent-account-verification-request-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
    },
    "zoom-urgent-account-update-required-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "spoof"],
    },
    "zoom-urgent-zoom-account-security-alert-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
    },
    "zoom-zoom-pro-subscription-offer-modified.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "punycode"],
    },
}
