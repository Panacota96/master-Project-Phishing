ANSWER_KEY = {
    # ─── 1. FAKE INVOICE ──────────────────────────────────────────────────────
    "fakeinvoice-urgency-spoofing-socialeng.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "urgency", "spoof"],
        "display": "fake invoice, urgency, spoofing",
        "flag": "THM{yougotnumber1-keep-it-going}",
    },
    "invoice-2.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "urgency", "spoof"],
        "display": "fake invoice, urgency, spoofing",
        "flag": "THM{inv-2-success-123}",
    },
    "invoice-3.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "attachment", "impersonation"],
        "display": "fake invoice, attachment, impersonation",
        "flag": "THM{inv-3-success-456}",
    },
    "invoice-4.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "externaldomain", "socialeng"],
        "display": "fake invoice, external domain, social engineering",
        "flag": "THM{inv-4-success-789}",
    },

    # ─── 2. IMPERSONATION ─────────────────────────────────────────────────────
    "impersonation-attachment-socialeng-spoof.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "attachment", "spoof"],
        "display": "impersonation, attachment, spoof",
        "flag": "THM{nmumber2-was-not-tha-thard!}",
    },
    "impersonation-2.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "urgency"],
        "display": "impersonation, social engineering, urgency",
        "flag": "THM{imp-2-success-987}",
    },
    "impersonation-3.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "attachment", "spoof"],
        "display": "impersonation, attachment, spoofing",
        "flag": "THM{imp-3-success-654}",
    },
    "impersonation-4.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "sidechannel", "socialeng"],
        "display": "impersonation, side channel, social engineering",
        "flag": "THM{imp-4-success-321}",
    },

    # ─── 3. IMPERSONATION URGENCY ─────────────────────────────────────────────
    "impersonation-socialeng-urgency.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "urgency"],
        "display": "impersonation, socialeng, urgency",
        "flag": "THM{Impersonation-is-areal-thing-keepIt}",
    },
    "urgency-2.eml": {
        "classification": "Phishing",
        "signals": ["urgency", "spoof", "socialeng"],
        "display": "urgency, spoofing, social engineering",
        "flag": "THM{urg-2-success-abc}",
    },
    "urgency-3.eml": {
        "classification": "Phishing",
        "signals": ["urgency", "punycode", "spoof"],
        "display": "urgency, punycode, spoofing",
        "flag": "THM{urg-3-success-def}",
    },
    "urgency-4.eml": {
        "classification": "Phishing",
        "signals": ["urgency", "fakelogin", "impersonation"],
        "display": "urgency, fake login, impersonation",
        "flag": "THM{urg-4-success-ghi}",
    },

    # ─── 4. LEGIT APP IMPERSONATION ───────────────────────────────────────────
    "legitapp-impersonation-externaldomain-socialeng.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "externaldomain", "socialeng"],
        "display": "impersonation, externaldomain, social engineering",
        "flag": "THM{Get-back-SOC-mas!!}",
    },
    "legit-app-2.eml": {
        "classification": "Phishing",
        "signals": ["fakelogin", "urgency", "spoof"],
        "display": "fake login, urgency, spoofing",
        "flag": "THM{legit-2-success-jkl}",
    },
    "legit-app-3.eml": {
        "classification": "Phishing",
        "signals": ["externaldomain", "socialeng", "impersonation"],
        "display": "external domain, social engineering, impersonation",
        "flag": "THM{legit-3-success-mno}",
    },
    "legit-app-4.eml": {
        "classification": "Phishing",
        "signals": ["attachment", "socialeng", "spoof"],
        "display": "attachment, social engineering, spoofing",
        "flag": "THM{legit-4-success-pqr}",
    },

    # ─── 5. PUNYCODE ──────────────────────────────────────────────────────────
    "punycode-impersonation-legitapp-socialeng.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "impersonation", "socialeng"],
        "display": "punycode, impersonation, social engineering",
        "flag": "THM{number6-is-the-last-one!-DX!}",
    },
    "punycode-2.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "impersonation", "socialeng"],
        "display": "punycode, impersonation, social engineering",
        "flag": "THM{puny-2-success-stu}",
    },
    "punycode-3.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "urgency", "spoof"],
        "display": "punycode, urgency, spoofing",
        "flag": "THM{puny-3-success-vwx}",
    },
    "punycode-4.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "fakelogin", "externaldomain"],
        "display": "punycode, fake login, external domain",
        "flag": "THM{puny-4-success-yz1}",
    },

    # ─── 6. SPAM ──────────────────────────────────────────────────────────────
    "marketing-spam-logistics.eml": {
        "classification": "Spam",
        "signals": [],
        "display": "spam",
        "flag": "THM{It-was-just-a-sp4m!!}",
    },
    "spam-2.eml": {
        "classification": "Spam",
        "signals": [],
        "display": "spam",
        "flag": "THM{It-was-just-a-sp4m!!}",
    },
    "spam-3.eml": {
        "classification": "Spam",
        "signals": [],
        "display": "spam",
        "flag": "THM{It-was-just-a-sp4m!!}",
    },
    "spam-4.eml": {
        "classification": "Spam",
        "signals": [],
        "display": "spam",
        "flag": "THM{It-was-just-a-sp4m!!}",
    },
    "phishing-attachment-1.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "attachment", "urgency"],
        "display": "impersonation, attachment, urgency",
        "flag": "THM{attachment-1-phish-success}",
    },
    "phishing-attachment-2.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "attachment", "urgency"],
        "display": "fake invoice, attachment, urgency",
        "flag": "THM{attachment-2-phish-success}",
    },
    "spam-attachment-1.eml": {
        "classification": "Spam",
        "signals": [],
        "display": "spam",
        "flag": "THM{It-was-just-a-sp4m!!}",
    },
    "spam-attachment-2.eml": {
        "classification": "Spam",
        "signals": [],
        "display": "spam",
        "flag": "THM{It-was-just-a-sp4m!!}",
    },
    "pixel-tracking.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "sidechannel"],
        "display": "impersonation, social engineering, side channel",
        "flag": "THM{pixel-tracking-success}",
    },
    "thread-hijacking.eml": {
        "classification": "Phishing",
        "signals": ["urgency", "socialeng", "spoof"],
        "display": "urgency, social engineering, spoofing",
        "flag": "THM{thread-hijacking-success}",
    },
    "subtle-typo.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "urgency", "spoof"],
        "display": "fake invoice, urgency, spoofing",
        "flag": "THM{subtle-typo-success}",
    },
    "homograph-attack.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "impersonation", "urgency"],
        "display": "punycode, impersonation, urgency",
        "flag": "THM{homograph-attack-success}",
    },
    "qr-phishing.eml": {
        "classification": "Phishing",
        "signals": ["fakelogin", "impersonation", "socialeng"],
        "display": "fake login, impersonation, social engineering",
        "flag": "THM{qr-phishing-success}",
    },
}
