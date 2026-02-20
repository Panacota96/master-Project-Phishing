ANSWER_KEY = {
    # ─── 1. FAKE INVOICE ──────────────────────────────────────────────────────
    "fakeinvoice-urgency-spoofing-socialeng.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "urgency", "spoof"],
        "explanation": (
            "This email uses a fake PayPal invoice to create panic. Note the spoofed 'From' address "
            "and the extreme urgency used to force a quick payment."
        ),
    },
    "invoice-2.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "urgency", "spoof"],
        "explanation": (
            "A classic 'payment declined' scam. The email mimics Microsoft branding but uses a "
            "non-Microsoft domain and threatens immediate data deletion."
        ),
    },
    "invoice-3.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "externaldomain", "impersonation"],
        "explanation": (
            "This FedEx impersonation uses a high-quality template to demand 'customs fees'. "
            "The tracking number is fake and the link leads to a non-FedEx domain."
        ),
    },
    "invoice-4.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "fakeinvoice", "externaldomain"],
        "explanation": (
            "An authentic-looking Apple receipt. Phishers use high-value 'purchases' to trick you "
            "into clicking 'Report a Problem' to steal your Apple ID credentials."
        ),
    },

    # ─── 2. IMPERSONATION ─────────────────────────────────────────────────────
    "impersonation-attachment-socialeng-spoof.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "attachment", "spoof"],
        "explanation": (
            "This email pretends to be a voice message notification. The HTML attachment is a "
            "credential harvester designed to look like an audio player."
        ),
    },
    "impersonation-2.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "externaldomain", "socialeng"],
        "explanation": (
            "Microsoft SharePoint sharing alerts are a common entry point. Note that the sender "
            "domain does not match the official SharePoint service."
        ),
    },
    "impersonation-3.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "externaldomain"],
        "explanation": (
            "A fake Zoom invitation. It uses curiosity about 'Internal Restructuring' to bait "
            "employees into clicking a malicious registration link."
        ),
    },
    "impersonation-4.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "spoof"],
        "explanation": (
            "IT Helpdesk impersonation. It asks you to 'rate your experience' via a link that "
            "actually captures your corporate login session."
        ),
    },

    # ─── 3. IMPERSONATION URGENCY ─────────────────────────────────────────────
    "impersonation-socialeng-urgency.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "urgency"],
        "explanation": (
            "This high-pressure email uses a 'Security Incident' as a cover to request unauthorized "
            "VPN access. Real IT will never ask for credentials via email."
        ),
    },
    "urgency-2.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "urgency"],
        "explanation": (
            "A DocuSign lure. The vague document name 'Internal_Audit_Requirements' is designed "
            "to make financial staff click without thinking."
        ),
    },
    "urgency-3.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
        "explanation": (
            "OneDrive storage alerts are effective because they threaten 'file deletion'. "
            "Check the link—it does not point to a microsoft.com domain."
        ),
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
        "explanation": (
            "Slack app authorization requests are a modern phishing tactic. The 'Deep-Research-AI' "
            "app is fake, and the link captures your workspace token."
        ),
    },
    "legit-app-3.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "urgency", "externaldomain"],
        "explanation": (
            "Adobe ID alerts about 'password resets' trick users into clicking a fake security link. "
            "Notice the sender domain is adobe.com.security-service.net."
        ),
    },
    "legit-app-4.eml": {
        "classification": "Phishing",
        "signals": ["attachment", "socialeng", "spoof"],
        "explanation": (
            "A fake insurance reminder with a malicious attachment. The .exe extension hidden "
            "in the filename is a clear red flag."
        ),
    },

    # ─── 5. PUNYCODE ──────────────────────────────────────────────────────────
    "punycode-impersonation-legitapp-socialeng.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "impersonation", "socialeng"],
        "explanation": (
            "This email uses a Punycode domain that looks identical to a real brand but contains "
            "non-standard characters to redirect you to a malicious site."
        ),
    },
    "punycode-2.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "impersonation", "externaldomain"],
        "explanation": (
            "Google security alerts using 'googIe.com' (with a capital I) instead of 'google.com' "
            "are classic examples of typosquatting and Punycode deception."
        ),
    },
    "punycode-3.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "urgency", "spoof"],
        "explanation": (
            "Another Punycode attack. The sense of urgency is used to prevent the user from "
            "carefully inspecting the suspicious URL."
        ),
    },
    "punycode-4.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "fakelogin", "externaldomain"],
        "explanation": (
            "Combining Punycode with a fake login page. The domain looks right at a glance, "
            "but leads to a credential harvesting portal."
        ),
    },

    # ─── 6. SPAM ──────────────────────────────────────────────────────────────
    "marketing-spam-logistics.eml": {
        "classification": "Spam",
        "signals": [],
        "explanation": (
            "This is legitimate unsolicited marketing (Spam). While annoying, it does not use "
            "deception, fake links, or malicious attachments."
        ),
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
        "explanation": (
            "This email impersonates internal payroll and uses a double extension (.doc.zip) "
            "to hide the true nature of the attachment."
        ),
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
