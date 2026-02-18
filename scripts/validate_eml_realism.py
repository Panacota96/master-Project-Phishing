#!/usr/bin/env python3
"""Validate .eml realism checklist (HTML, text, links, images, attachments)."""

from __future__ import annotations

import argparse
import json
import re
from email import policy
from email.parser import BytesParser
from pathlib import Path


RE_LINK = re.compile(r'href=["\\\']([^"\\\']+)')
RE_IMG = re.compile(r'<img\\s+[^>]*src=["\\\']([^"\\\']+)')


def parse_eml(path: Path):
    with path.open('rb') as handle:
        return BytesParser(policy=policy.default).parse(handle)


def extract_parts(msg):
    text_body = ''
    html_body = ''
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get('Content-Disposition', ''))
            filename = part.get_filename()

            if content_type == 'text/plain' and 'attachment' not in disposition:
                payload = part.get_content()
                if isinstance(payload, str):
                    text_body += payload
            elif content_type == 'text/html' and 'attachment' not in disposition:
                payload = part.get_content()
                if isinstance(payload, str):
                    html_body += payload
            elif filename or 'attachment' in disposition:
                attachments.append({
                    'filename': filename,
                    'content_type': content_type,
                })
    else:
        if msg.get_content_type() == 'text/plain':
            text_body = msg.get_content()
        elif msg.get_content_type() == 'text/html':
            html_body = msg.get_content()

    links = RE_LINK.findall(html_body) if html_body else []
    images = RE_IMG.findall(html_body) if html_body else []
    image_attachments = [a for a in attachments if (a['content_type'] or '').startswith('image/')]

    return {
        'text': text_body,
        'html': html_body,
        'links': links,
        'images': images,
        'attachments': attachments,
        'image_attachments': image_attachments,
    }


def load_allowlist(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text() or '{}')
    return data if isinstance(data, dict) else {}

def resolve_allowlist(path: Path, allowlist: dict) -> dict:
    defaults = allowlist.get('defaults', {})
    paths = allowlist.get('paths', {})
    files = allowlist.get('files', {})

    resolved = dict(defaults)
    for prefix, overrides in paths.items():
        if str(path).startswith(prefix):
            resolved.update(overrides)
    resolved.update(files.get(path.name, {}))
    return resolved


def validate_eml(path: Path, allowlist: dict):
    msg = parse_eml(path)
    parts = extract_parts(msg)
    skip = resolve_allowlist(path, allowlist)

    failures = []
    has_text = bool(parts['text'].strip())
    has_html = bool(parts['html'].strip())
    has_links = bool(parts['links'])
    has_attachments = bool(parts['attachments'])
    has_images = bool(parts['images'] or parts['image_attachments'])

    if not skip.get('skip_text_html', False) and not (has_text or has_html):
        failures.append('missing text/plain and text/html')
    if not skip.get('skip_link_attachment', False) and not (has_links or has_attachments):
        failures.append('missing links and attachments')

    warnings = []
    if not skip.get('skip_image', False) and not has_images:
        warnings.append('missing images')
    if skip.get('require_attachment', False) and not has_attachments:
        failures.append('missing attachment')

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='examples', help='Root folder to scan for .eml')
    parser.add_argument('--allowlist', default='examples/realism_allowlist.json')
    parser.add_argument('--report', default='examples/realism_report.json', help='Path to write JSON report')
    args = parser.parse_args()

    root = Path(args.root)
    allowlist = load_allowlist(Path(args.allowlist))

    failures = {}
    warnings = {}
    for path in root.rglob('*.eml'):
        errors, warns = validate_eml(path, allowlist)
        if errors:
            failures[str(path)] = errors
        if warns:
            warnings[str(path)] = warns

    report_path = Path(args.report)
    report_payload = {
        'failures': failures,
        'warnings': warnings,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report_payload, indent=2))

    if warnings:
        print('Realism warnings:')
        for path, issues in sorted(warnings.items()):
            print(f'- {path}: {", ".join(issues)}')

    if failures:
        print('Realism validation failed:')
        for path, issues in sorted(failures.items()):
            print(f'- {path}: {", ".join(issues)}')
        return 1

    print('Realism validation passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
