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
        "signals": ["fakeinvoice", "attachment", "impersonation"],
    },
    "invoice-4.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "externaldomain", "socialeng"],
    },

    # ─── 2. IMPERSONATION ─────────────────────────────────────────────────────
    "impersonation-attachment-socialeng-spoof.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "attachment", "spoof"],
    },
    "impersonation-2.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "urgency"],
    },
    "impersonation-3.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "attachment", "spoof"],
    },
    "impersonation-4.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "sidechannel", "socialeng"],
    },

    # ─── 3. IMPERSONATION URGENCY ─────────────────────────────────────────────
    "impersonation-socialeng-urgency.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "urgency"],
    },
    "urgency-2.eml": {
        "classification": "Phishing",
        "signals": ["urgency", "spoof", "socialeng"],
    },
    "urgency-3.eml": {
        "classification": "Phishing",
        "signals": ["urgency", "punycode", "spoof"],
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
        "signals": ["fakelogin", "urgency", "spoof"],
    },
    "legit-app-3.eml": {
        "classification": "Phishing",
        "signals": ["externaldomain", "socialeng", "impersonation"],
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
        "signals": ["punycode", "impersonation", "socialeng"],
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
}
