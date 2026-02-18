ANSWER_KEY = {
    "fakeinvoice-urgency-spoofing-socialeng.eml": {
        "classification": "Phishing",
        "signals": ["fakeinvoice", "urgency", "spoof"],
        "display": "fakeinvoice, urgency, spoofing",
        "flag": "THM{yougotnumber1-keep-it-going}",
    },
    "impersonation-attachment-socialeng-spoof.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "attachment", "spoof"],
        "display": "impersonation, attachment, spoof",
        "flag": "THM{nmumber2-was-not-tha-thard!}",
    },
    "impersonation-socialeng-urgency.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "socialeng", "urgency"],
        "display": "impersonation, socialeng, urgency",
        "flag": "THM{Impersonation-is-areal-thing-keepIt}",
    },
    "legitapp-impersonation-externaldomain-socialeng.eml": {
        "classification": "Phishing",
        "signals": ["impersonation", "externaldomain", "socialeng"],
        "display": "impersonation, externaldomain, social engineering",
        "flag": "THM{Get-back-SOC-mas!!}",
    },
    "marketing-spam-logistics.eml": {
        "classification": "Spam",
        "signals": [],
        "display": "spam",
        "flag": "THM{It-was-just-a-sp4m!!}",
    },
    "punycode-impersonation-legitapp-socialeng.eml": {
        "classification": "Phishing",
        "signals": ["punycode", "impersonation", "socialeng"],
        "display": "punycode, impersonation, social engineering",
        "flag": "THM{number6-is-the-last-one!-DX!}",
    },
}
