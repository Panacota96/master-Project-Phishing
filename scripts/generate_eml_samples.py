#!/usr/bin/env python3
"""Generate realistic .eml samples with multipart bodies and headers."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from uuid import uuid4
import base64


BASE64_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAgcB"
    "9l9n1QAAAABJRU5ErkJggg=="
)

BASE64_PDF = (
    "JVBERi0xLjQKJcTl8uXrp/Og0MTGCjEgMCBvYmoKPDwvVHlwZS9DYXRhbG9nPj4KZW5k"
    "b2JqCjIgMCBvYmoKPDwvVHlwZS9QYWdlPj4KZW5kb2JqCnhyZWYKMCAzCjAwMDAwMDAw"
    "MDAgNjU1MzUgZiAKMDAwMDAwMDAxMCAwMDAwMCBuIAowMDAwMDAwMDUyIDAwMDAwIG4g"
    "CnRyYWlsZXIKPDwvUm9vdCAxIDAgUj4+CnN0YXJ0eHJlZgo2NQolJUVPRgo="
)


def build_message(subject: str, from_addr: str, to_addr: str, link: str, output_name: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    msg["Message-ID"] = f"<{uuid4().hex}@example.com>"
    msg["Reply-To"] = from_addr
    msg["Return-Path"] = "bounce@example.com"
    msg["MIME-Version"] = "1.0"
    msg["Authentication-Results"] = (
        "mx.example.edu; spf=softfail smtp.mailfrom=example.com; dkim=pass; dmarc=fail"
    )
    msg["Received"] = "from mail.example.com (203.0.113.77) by mx.example.edu with ESMTPS id GEN1"

    text_body = (
        "Hello,\n\n"
        "Please review the notification and take action.\n\n"
        f"Link: {link}\n\n"
        "If you prefer, scan the QR code in the email.\n"
    )
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1f2937;">
        <h2>{subject}</h2>
        <p>Please review the notification and take action.</p>
        <p>
          <a href="{link}"
             style="display:inline-block;padding:10px 16px;background:#2563eb;color:#fff;text-decoration:none;border-radius:4px;">
            Open Portal
          </a>
        </p>
        <p>Scan the QR code:</p>
        <img src="cid:qr-code" alt="QR" width="140" height="140" />
        <img src="cid:logo" alt="Logo" width="120" height="32" />
        <img src="https://tracking.example.com/pixel?id=GEN" width="1" height="1" alt="" />
      </body>
    </html>
    """

    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    msg.get_payload()[1].add_related(
        base64.b64decode(BASE64_PNG),
        maintype="image",
        subtype="png",
        cid="logo",
        filename="logo.png",
    )
    msg.get_payload()[1].add_related(
        base64.b64decode(BASE64_PNG),
        maintype="image",
        subtype="png",
        cid="qr-code",
        filename="qr.png",
    )
    msg.add_attachment(
        base64.b64decode(BASE64_PDF),
        maintype="application",
        subtype="pdf",
        filename=f"{output_name}.pdf",
    )
    return msg


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate realistic .eml samples.")
    parser.add_argument("--count", type=int, default=3, help="Number of .eml files to generate")
    parser.add_argument("--out-dir", default="examples/generated", help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i in range(args.count):
        name = f"generated-{i + 1:02d}"
        msg = build_message(
            subject=f"Account Action Required {i + 1}",
            from_addr="Security Team <security@example.com>",
            to_addr="User <user@example.com>",
            link=f"https://example.com.secure-login.net/action/{i + 1}",
            output_name=name,
        )
        (out_dir / f"{name}.eml").write_text(msg.as_string())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
