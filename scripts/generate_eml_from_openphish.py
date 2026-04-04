#!/usr/bin/env python3
"""Generate .eml samples from the OpenPhish feed (defanged URLs)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

import requests


def guess_target(url: str) -> str:
    lowered = url.lower()
    if 'microsoft' in lowered or 'office' in lowered or 'sharepoint' in lowered:
        return 'Microsoft 365'
    if 'google' in lowered or 'gmail' in lowered:
        return 'Google'
    if 'amazon' in lowered or 'aws' in lowered:
        return 'Amazon'
    if 'paypal' in lowered:
        return 'PayPal'
    if 'apple' in lowered or 'icloud' in lowered:
        return 'Apple'
    return 'Unknown'


def defang(url: str) -> str:
    return url.replace('http', 'hxxp').replace('.', '[.]')


def fetch_urls(feed_url: str, limit: int) -> list[str]:
    resp = requests.get(feed_url, timeout=5)
    resp.raise_for_status()
    urls = [line.strip() for line in resp.text.splitlines() if line.strip()]
    return urls[:limit]


def build_message(raw_url: str, defanged: str, target: str, index: int) -> EmailMessage:
    msg = EmailMessage()
    msg['From'] = f"Threat Intel <alerts@openphish.example>"
    msg['To'] = "Security Team <security@esme.edu>"
    msg['Subject'] = f"[OpenPhish] Malicious URL #{index}: {target}"
    msg['Date'] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    msg['Message-ID'] = f"<openphish-{index}@openphish.example>"
    msg['MIME-Version'] = "1.0"
    msg['Authentication-Results'] = "mx.esme.edu; spf=neutral smtp.mailfrom=openphish.example"

    text_body = (
        "A malicious URL was observed on the OpenPhish feed.\n\n"
        f"Target: {target}\n"
        f"Raw URL: {raw_url}\n"
        f"Defanged: {defanged}\n\n"
        "Use this sample to train users in the Email Threat Inspector."
    )
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #111827;">
        <p>A malicious URL was observed on the <strong>OpenPhish</strong> feed.</p>
        <ul>
          <li><strong>Target:</strong> {target}</li>
          <li><strong>Raw URL:</strong> {raw_url}</li>
          <li><strong>Defanged:</strong> {defanged}</li>
        </ul>
        <p>Use this sample to train users in the Email Threat Inspector.</p>
        <p style="color:#6b7280;font-size:12px;">Generated automatically from OpenPhish feed.</p>
      </body>
    </html>
    """

    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    return msg


def generate(feed_url: str, out_dir: Path, limit: int, keep_raw: bool) -> Iterable[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    urls = fetch_urls(feed_url, limit)
    generated = []
    for idx, url in enumerate(urls, start=1):
        target = guess_target(url)
        safe = url if keep_raw else defang(url)
        msg = build_message(url, safe, target, idx)
        dest = out_dir / f"openphish-{idx:02d}.eml"
        dest.write_text(msg.as_string())
        generated.append(dest)
    return generated


def main() -> int:
    parser = argparse.ArgumentParser(description="Create .eml samples from the OpenPhish feed.")
    parser.add_argument('--feed-url', default='https://openphish.com/feed.txt', help='OpenPhish feed URL')
    parser.add_argument('--out-dir', default='examples/openphish_samples', help='Where to write generated .eml files')
    parser.add_argument('--limit', type=int, default=5, help='Maximum URLs to convert')
    parser.add_argument('--keep-raw', action='store_true', help='Keep URLs unfanged (default: defang for safety)')
    args = parser.parse_args()

    out_path = Path(args.out_dir)
    try:
        generated = list(generate(args.feed_url, out_path, args.limit, args.keep_raw))
    except Exception as exc:
        print(f"Failed to generate samples: {exc}")
        return 1

    for path in generated:
        print(f"Generated: {path}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
