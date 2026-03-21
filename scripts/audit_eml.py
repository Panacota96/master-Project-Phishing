#!/usr/bin/env python3
"""
audit_eml.py — Compliance audit for EML training files.

For each EML in examples/ that has an ANSWER_KEY entry, checks whether the
email content actually demonstrates the required phishing signals. Produces a
markdown report at examples/compliance_report.md.

Usage:
    python scripts/audit_eml.py [--verbose]
"""
import re
import sys
import email as emaillib
import email.policy
import base64
import json
from pathlib import Path

ROOT      = Path(__file__).parent.parent
EXAMPLES  = ROOT / "examples"
REPORT    = EXAMPLES / "compliance_report.md"
AK_FILE   = ROOT / "app" / "inspector" / "answer_key.py"

# ---------------------------------------------------------------------------
# Load ANSWER_KEY from answer_key.py by parsing it with exec()
# ---------------------------------------------------------------------------

def load_answer_key() -> dict:
    ns: dict = {}
    exec(AK_FILE.read_text(encoding="utf-8"), ns)  # noqa: S102
    return ns["ANSWER_KEY"]


# ---------------------------------------------------------------------------
# Signal detectors  (content = full raw EML text, lowercased)
# ---------------------------------------------------------------------------

URGENCY_WORDS = [
    "immediately", "urgent", "urgently", "expire", "expir", "within 24",
    "within 48", "action required", "act now", "limited time", "as soon as",
    "critical", "suspend", "terminate", "deadline",
]
SOCIALENG_WORDS = [
    "your account", "verify", "confirm", "suspicious", "unusual activity",
    "click here", "click below", "click the link", "limited offer",
    "congratulations", "you have been selected", "bonus", "reward",
    "we noticed", "we detected",
]
FAKEINVOICE_WORDS = [
    "invoice", "payment", "billing", "receipt", "charge", "refund",
    "overdue", "amount due", "total due", "pay now", "subscription",
]
FAKELOGIN_WORDS = [
    "sign in", "log in", "login", "verify your account", "enter your",
    "reset your password", "update your credentials", "access your account",
]


def _body(raw: str) -> str:
    """Return lowercased concatenation of text/plain + text/html body parts."""
    try:
        msg = emaillib.message_from_string(raw, policy=emaillib.policy.compat32)
        parts = []
        for part in msg.walk():
            ct = part.get_content_type()
            if ct in ("text/plain", "text/html"):
                payload = part.get_payload(decode=True)
                if payload:
                    parts.append(payload.decode("utf-8", errors="replace"))
        return " ".join(parts).lower()
    except Exception:
        return raw.lower()


def _headers(raw: str) -> dict:
    """Return lower-cased dict of key header fields."""
    result: dict = {}
    for line in raw.splitlines():
        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            k, _, v = line.partition(":")
            result[k.strip().lower()] = v.strip().lower()
        if line == "":
            break
    return result


def _links(body_text: str) -> list[str]:
    return re.findall(r'href=["\']([^"\']+)', body_text, re.IGNORECASE)


def check_signal(signal: str, raw: str, headers: dict, body: str, links: list[str]) -> tuple[bool, str]:
    """Return (passed, reason)."""
    if signal == "impersonation":
        from_h = headers.get("from", "")
        subject = headers.get("subject", "")
        known_brands = [
            "microsoft", "google", "apple", "slack", "dhl", "fedex",
            "amazon", "ibm", "zoom", "cisco", "okta", "docusign", "adobe",
            "oracle", "paypal", "linkedin", "dropbox", "norton", "skype",
            "bluejeans", "gotomeeting", "ringcentral", "azure", "aws",
        ]
        for brand in known_brands:
            if brand in from_h or brand in subject or brand in body[:500]:
                return True, f"brand '{brand}' found"
        return False, "no recognizable brand found in From/Subject/body"

    if signal == "externaldomain":
        from_h = headers.get("from", "")
        # Extract domain from From
        m = re.search(r"@([\w.\-]+)", from_h)
        if not m:
            return False, "no domain in From header"
        from_domain = m.group(1)
        # Check if From domain differs from any link domain
        for link in links:
            m2 = re.search(r"https?://([\w.\-]+)", link)
            if m2 and m2.group(1) != from_domain:
                return True, f"link domain {m2.group(1)} != from domain {from_domain}"
        # Also check if From domain looks spoofed (brand in display name but attacker domain)
        if re.search(r'"[^"]*@', from_h):  # display name contains @
            return True, "display name contains @-address"
        if "example.com" in from_h or "phish" in from_h or "malicious" in from_h:
            return True, "obviously fake domain in From"
        # Check if the From domain doesn't match the brand claimed
        for brand in ["microsoft", "google", "apple", "slack", "amazon", "ibm"]:
            if brand in body[:300] and brand not in from_domain:
                return True, f"brand '{brand}' in body but From domain is {from_domain}"
        return False, f"could not confirm external domain (From: {from_domain})"

    if signal == "urgency":
        for w in URGENCY_WORDS:
            if w in body:
                return True, f"urgency word '{w}'"
        return False, "no urgency words found"

    if signal == "spoof":
        from_h   = headers.get("from", "")
        return_p = headers.get("return-path", "")
        if not return_p:
            return False, "no Return-Path header"
        m1 = re.search(r"@([\w.\-]+)", from_h)
        m2 = re.search(r"@([\w.\-]+)", return_p)
        if m1 and m2 and m1.group(1) != m2.group(1):
            return True, f"From domain {m1.group(1)} != Return-Path domain {m2.group(1)}"
        # Also check if From display name contains a different address
        if re.search(r'"[^"]*<[^>]+@[^>]+>"', headers.get("from", "")):
            return True, "display name wraps a different address"
        return False, f"From/Return-Path domains match or Return-Path absent"

    if signal == "socialeng":
        for w in SOCIALENG_WORDS:
            if w in body:
                return True, f"social engineering phrase '{w}'"
        return False, "no social engineering phrases found"

    if signal == "fakeinvoice":
        for w in FAKEINVOICE_WORDS:
            if w in body:
                return True, f"invoice-related word '{w}'"
        return False, "no invoice-related content found"

    if signal == "fakelogin":
        for w in FAKELOGIN_WORDS:
            if w in body:
                return True, f"login phrase '{w}'"
        if any("login" in l or "signin" in l or "verify" in l or "auth" in l for l in links):
            return True, "login/verify link found"
        return False, "no fake login indicators found"

    if signal == "attachment":
        # Check for MIME attachments (Content-Disposition: attachment)
        if "content-disposition: attachment" in raw.lower():
            return True, "MIME attachment present"
        if "filename=" in raw.lower():
            return True, "filename= in MIME headers"
        return False, "no attachment found"

    if signal == "punycode":
        if "xn--" in raw.lower():
            return True, "punycode (xn--) domain present"
        return False, "no xn-- punycode domain found"

    if signal == "sidechannel":
        if re.search(r"\+?\d[\d\s\-]{6,}", body):
            return True, "phone number pattern found"
        if "call us" in body or "call our" in body or "dial" in body:
            return True, "call/dial instruction found"
        return False, "no side-channel (phone) indicators found"

    return False, f"unknown signal '{signal}'"


# ---------------------------------------------------------------------------
# Main audit
# ---------------------------------------------------------------------------

def audit() -> None:
    verbose = "--verbose" in sys.argv
    answer_key = load_answer_key()

    # Map filename → path
    eml_map: dict[str, Path] = {}
    for p in EXAMPLES.rglob("*.eml"):
        eml_map[p.name] = p

    lines = [
        "# EML Compliance Audit Report",
        "",
        "Checks each training EML against its required ANSWER_KEY signals.",
        "**PASS** = signal detected | **WARN** = signal may be missing",
        "",
        f"| File | Classification | Signal | Status | Detail |",
        f"|------|---------------|--------|--------|--------|",
    ]

    total = pass_count = warn_count = 0

    for filename, entry in sorted(answer_key.items()):
        classification = entry.get("classification", "?")
        signals = entry.get("signals", [])

        path = eml_map.get(filename)
        if not path:
            lines.append(f"| `{filename}` | {classification} | — | ❌ NOT FOUND | file missing in examples/ |")
            continue

        raw = path.read_text(encoding="utf-8", errors="replace")
        headers = _headers(raw)
        body    = _body(raw)
        links   = _links(body)

        if not signals:
            lines.append(f"| `{filename}` | {classification} | — | ✅ PASS | Spam – no signals required |")
            pass_count += 1
            total += 1
            continue

        for sig in signals:
            total += 1
            ok, reason = check_signal(sig, raw, headers, body, links)
            status = "✅ PASS" if ok else "⚠️ WARN"
            if ok:
                pass_count += 1
                if verbose:
                    lines.append(f"| `{filename}` | {classification} | `{sig}` | {status} | {reason} |")
            else:
                warn_count += 1
                lines.append(f"| `{filename}` | {classification} | `{sig}` | {status} | {reason} |")

    lines += [
        "",
        f"## Summary",
        f"- **Total signal checks**: {total}",
        f"- **Pass**: {pass_count} ({100*pass_count//total if total else 0}%)",
        f"- **Warn**: {warn_count}",
    ]

    report_text = "\n".join(lines)
    REPORT.write_text(report_text, encoding="utf-8")
    print(f"Report written to {REPORT}")
    print(f"Total: {total} | Pass: {pass_count} | Warn: {warn_count}")


if __name__ == "__main__":
    audit()
