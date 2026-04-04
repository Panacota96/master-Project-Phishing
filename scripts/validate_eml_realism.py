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


def parse_json_eml(path: Path):
    try:
        raw = path.read_text(errors='ignore').lstrip()
        if not raw.startswith('{'):
            return None
        return json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def extract_parts(msg):
    text_body = ''
    html_body = ''
    attachments = []

    headers = {k.lower(): v for k, v in msg.items()}

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
    non_inline_attachments = [a for a in attachments if a not in image_attachments]

    return {
        'text': text_body,
        'html': html_body,
        'links': links,
        'images': images,
        'attachments': attachments,
        'image_attachments': image_attachments,
        'non_inline_attachments': non_inline_attachments,
        'headers': headers,
    }


def extract_parts_from_json(obj: dict):
    text_body = obj.get('textBody', '') or ''
    html_body = obj.get('htmlBody', '') or ''
    links = obj.get('links') or []
    attachments = obj.get('attachments') or []
    images = RE_IMG.findall(html_body) if html_body else []
    inline_images = obj.get('inlineImages') or {}
    image_attachments = [{'content_type': 'image/*'} for _ in inline_images] if inline_images else []
    non_inline_attachments = [a for a in attachments if (a.get('contentType') or '').startswith('image/') is False]

    if not links and html_body:
        links = RE_LINK.findall(html_body)

    return {
        'text': text_body,
        'html': html_body,
        'links': links,
        'images': images,
        'attachments': attachments,
        'image_attachments': image_attachments,
        'non_inline_attachments': non_inline_attachments,
        'headers': {k.lower(): v for k, v in (obj.get('headers') or {}).items()},
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
    json_obj = parse_json_eml(path)
    if json_obj is not None:
        parts = extract_parts_from_json(json_obj)
    else:
        msg = parse_eml(path)
        parts = extract_parts(msg)
    skip = resolve_allowlist(path, allowlist)

    failures = []
    has_text = bool(parts['text'].strip())
    has_html = bool(parts['html'].strip())
    has_links = bool(parts['links'])
    has_attachments = bool(parts.get('non_inline_attachments'))
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

    score, score_notes = score_parts(parts)
    warnings.extend(score_notes)

    min_score = skip.get('min_score_override', None)
    if min_score is None:
        min_score = allowlist.get('min_score', 50)
    try:
        min_score_int = int(min_score)
    except (TypeError, ValueError):
        min_score_int = 50

    if score < min_score_int and not skip.get('skip_min_score', False):
        failures.append(f'realism score {score} below minimum {min_score_int}')

    return failures, warnings, score


def score_parts(parts: dict):
    """Compute a simple realism score out of 100 based on structure richness."""
    score = 0
    notes = []

    has_text = bool(parts.get('text', '').strip())
    has_html = bool(parts.get('html', '').strip())
    has_links = bool(parts.get('links'))
    has_attachments = bool(parts.get('non_inline_attachments'))
    has_images = bool(parts.get('images') or parts.get('image_attachments'))
    headers = parts.get('headers') or {}

    if has_text and has_html:
        score += 20
    elif has_html or has_text:
        score += 10
        notes.append('only one body part present')
    else:
        notes.append('no body content detected')

    if has_links:
        score += 20
    else:
        notes.append('no hyperlinks present')

    if has_images:
        score += 10
    else:
        notes.append('no inline images found')

    if has_attachments:
        score += 15
    else:
        notes.append('no downloadable attachments detected')

    if headers.get('authentication-results') or headers.get('dkim-signature') or headers.get('received-spf'):
        score += 10
    else:
        notes.append('no authentication headers (DKIM/SPF) present')

    if headers.get('message-id'):
        score += 5
    else:
        notes.append('missing Message-ID header')

    if headers.get('return-path') or headers.get('reply-to'):
        score += 5

    if headers.get('received'):
        score += 5
    else:
        notes.append('no Received headers found')

    return min(score, 100), notes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='examples', help='Root folder to scan for .eml')
    parser.add_argument('--allowlist', default='examples/realism_allowlist.json')
    parser.add_argument('--report', default='examples/realism_report.json', help='Path to write JSON report')
    parser.add_argument('--min-score', type=int, default=50, help='Minimum realism score to pass')
    args = parser.parse_args()

    root = Path(args.root)
    allowlist = load_allowlist(Path(args.allowlist))
    allowlist.setdefault('min_score', args.min_score)

    failures = {}
    warnings = {}
    scores = {}
    for path in root.rglob('*.eml'):
        errors, warns, score = validate_eml(path, allowlist)
        if errors:
            failures[str(path)] = errors
        if warns:
            warnings[str(path)] = warns
        scores[str(path)] = score

    report_path = Path(args.report)
    report_payload = {
        'failures': failures,
        'warnings': warnings,
        'scores': scores,
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
