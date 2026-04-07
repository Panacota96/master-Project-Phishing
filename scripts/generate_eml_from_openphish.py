#!/usr/bin/env python3
"""
generate_eml_from_openphish.py — build .eml samples from OpenPhish URLs.

Fetches the public OpenPhish feed (https://openphish.com/feed.txt), picks
a configurable number of phishing URLs at random, and wraps each one in a
realistic multipart/alternative .eml file that can be uploaded to S3 and
used by the Email Threat Inspector.

Usage
-----
    python scripts/generate_eml_from_openphish.py \
        --count 5 \
        --output examples/openphish \
        [--seed 42]

Each generated file is also printed to stdout along with a suggested
``answer_key.py`` snippet so you can paste it directly.

Requirements
------------
- requests (already in requirements.txt)
- No real AWS credentials needed; this only creates local .eml files.
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

try:
    import requests
except ImportError:
    print("ERROR: 'requests' is required — pip install requests", file=sys.stderr)
    sys.exit(1)

FEED_URL = "https://openphish.com/feed.txt"
DEFAULT_COUNT = 5
DEFAULT_OUTPUT = "examples/openphish"

# Sender and recipient placeholders used in the generated EML bodies
FAKE_FROM_NAME = "Security Notification"
FAKE_FROM_DOMAIN = "secure-alerts.example.net"
FAKE_TO = "student@university.example.edu"

SIGNAL_POOL = [
    "impersonation",
    "fakelogin",
    "urgency",
    "socialeng",
    "externaldomain",
    "spoof",
    "punycode",
]


def fetch_feed(url: str = FEED_URL, timeout: int = 10) -> list[str]:
    """Download the OpenPhish feed and return a deduplicated list of URLs."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"WARNING: Could not fetch OpenPhish feed ({exc}). Using stub URL.", file=sys.stderr)
        return ["https://phishing.example.com/login"]
    lines = [line.strip() for line in resp.text.splitlines() if line.strip().startswith("http")]
    return list(dict.fromkeys(lines))  # deduplicate while preserving order


def _infer_brand(url: str) -> str:
    """Guess the impersonated brand from the URL hostname."""
    host = urlparse(url).netloc.lower()
    brands = {
        "microsoft": "Microsoft",
        "office": "Microsoft 365",
        "outlook": "Outlook",
        "apple": "Apple",
        "paypal": "PayPal",
        "amazon": "Amazon",
        "google": "Google",
        "facebook": "Facebook",
        "dhl": "DHL",
        "fedex": "FedEx",
        "netflix": "Netflix",
        "dropbox": "Dropbox",
        "docusign": "DocuSign",
    }
    for keyword, name in brands.items():
        if keyword in host:
            return name
    return "IT Support"


def _pick_signals(url: str) -> list[str]:
    """Return 3 plausible signals for a given URL."""
    host = urlparse(url).netloc.lower()
    signals = ["impersonation"]
    # Detect punycode-ish or suspicious characters
    if re.search(r"xn--|[^\x00-\x7f]", host):
        signals.append("punycode")
    else:
        signals.append("fakelogin")
    # Third signal based on URL length / depth
    path = urlparse(url).path
    if len(path) > 30 or path.count("/") > 3:
        signals.append("externaldomain")
    else:
        signals.append("urgency")
    return signals[:3]


def build_eml(phishing_url: str, index: int) -> tuple[str, EmailMessage]:
    """
    Wrap a phishing URL in a realistic multipart/alternative EML.

    Returns (suggested_filename, EmailMessage).
    """
    brand = _infer_brand(phishing_url)
    host = urlparse(phishing_url).netloc or "unknown-domain.com"
    subject = f"[Action Required] Verify your {brand} account immediately"
    from_addr = f"noreply@{FAKE_FROM_DOMAIN}"
    msg_id = uuid4().hex

    msg = EmailMessage()
    msg["From"] = f"{FAKE_FROM_NAME} <{from_addr}>"
    msg["To"] = FAKE_TO
    msg["Subject"] = subject
    msg["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    msg["Message-ID"] = f"<{msg_id}@{FAKE_FROM_DOMAIN}>"
    msg["Reply-To"] = from_addr
    msg["Return-Path"] = f"bounce@{FAKE_FROM_DOMAIN}"
    msg["MIME-Version"] = "1.0"
    msg["Authentication-Results"] = (
        f"mx.university.example.edu; spf=fail smtp.mailfrom={FAKE_FROM_DOMAIN}; "
        "dkim=none; dmarc=fail policy=reject"
    )
    msg["X-Mailer"] = "OpenPhish-EML-Generator/1.0"
    msg["X-Source-URL"] = phishing_url

    text_body = (
        f"Dear User,\n\n"
        f"We have detected unusual activity on your {brand} account.\n"
        f"Please verify your identity immediately to avoid account suspension.\n\n"
        f"Verify here: {phishing_url}\n\n"
        f"If you did not initiate this request, ignore this email.\n\n"
        f"Regards,\n{brand} Security Team"
    )
    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; background:#f3f4f6; padding:24px;">
  <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:8px;padding:32px;">
    <h2 style="color:#1e3a5f;">{brand} Security Alert</h2>
    <p>Dear User,</p>
    <p>We have detected <strong>unusual sign-in activity</strong> on your {brand} account.
       Please verify your identity <strong>immediately</strong> to avoid suspension.</p>
    <p style="text-align:center;margin:24px 0;">
      <a href="{phishing_url}"
         style="display:inline-block;padding:12px 24px;background:#d32f2f;color:#fff;
                text-decoration:none;border-radius:4px;font-weight:bold;">
        Verify My Account
      </a>
    </p>
    <p style="font-size:12px;color:#6b7280;">
      Sender domain: {host} &mdash; This email was generated for security training purposes.
    </p>
  </div>
</body>
</html>"""

    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    # Suggested filename based on brand and index
    safe_brand = re.sub(r"[^a-z0-9]+", "-", brand.lower()).strip("-")
    filename = f"openphish-{safe_brand}-{index:03d}.eml"
    return filename, msg


def _answer_key_snippet(filename: str, signals: list[str]) -> str:
    sig_repr = ", ".join(f'"{s}"' for s in signals)
    return (
        f'    "{filename}": {{\n'
        f'        "classification": "Phishing",\n'
        f'        "signals": [{sig_repr}],\n'
        f'    }},\n'
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate .eml phishing samples from the OpenPhish feed."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        help=f"Number of EML files to generate (default: {DEFAULT_COUNT})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible selection",
    )
    parser.add_argument(
        "--feed-url",
        default=FEED_URL,
        help=f"OpenPhish feed URL (default: {FEED_URL})",
    )
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching feed from {args.feed_url} …")
    urls = fetch_feed(args.feed_url)
    print(f"  → {len(urls)} URLs available")

    count = min(args.count, len(urls))
    selected = random.sample(urls, count) if len(urls) >= count else urls[:count]

    print(f"\nGenerating {count} EML file(s) in '{output_dir}/' …\n")
    snippets: list[str] = []

    for idx, url in enumerate(selected, start=1):
        filename, msg = build_eml(url, idx)
        signals = _pick_signals(url)
        out_path = output_dir / filename
        out_path.write_bytes(msg.as_bytes())
        print(f"  [{idx:02d}] {filename}")
        print(f"        URL     : {url}")
        print(f"        Signals : {signals}")
        snippets.append(_answer_key_snippet(filename, signals))

    print("\n─── answer_key.py snippet ───────────────────────────────────────────")
    for snippet in snippets:
        print(snippet, end="")
    print("─────────────────────────────────────────────────────────────────────")
    print("\nDone. Add the snippet above to app/inspector/answer_key.py,")
    print("then sync with: make sync-eml")


if __name__ == "__main__":
    main()
