import email
import email.policy
import os
import re

from flask import jsonify, render_template

from app.inspector import bp

EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'examples')


def _get_eml_files():
    """Walk the examples/ directory and return a list of .eml file paths."""
    eml_files = []
    if not os.path.isdir(EXAMPLES_DIR):
        return eml_files
    for root, _dirs, files in os.walk(EXAMPLES_DIR):
        for f in files:
            if f.lower().endswith('.eml'):
                eml_files.append(os.path.join(root, f))
    return sorted(eml_files)


def _find_eml_by_filename(filename):
    """Find an .eml file by its basename, ensuring it's inside examples/."""
    # Prevent path traversal
    basename = os.path.basename(filename)
    if basename != filename or '..' in filename:
        return None
    for filepath in _get_eml_files():
        if os.path.basename(filepath) == basename:
            return filepath
    return None


def _parse_eml_summary(filepath):
    """Parse an .eml file and return summary info for the list view."""
    with open(filepath, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=email.policy.default)
    return {
        'fileName': os.path.basename(filepath),
        'subject': msg.get('Subject', '(no subject)'),
        'from': msg.get('From', ''),
        'to': msg.get('To', ''),
        'date': msg.get('Date', ''),
    }


def _parse_eml_detail(filepath):
    """Parse an .eml file and return full details for the detail view."""
    with open(filepath, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=email.policy.default)

    filename = os.path.basename(filepath)
    summary = {
        'fileName': filename,
        'subject': msg.get('Subject', '(no subject)'),
        'from': msg.get('From', ''),
        'to': msg.get('To', ''),
        'date': msg.get('Date', ''),
    }

    # Extract headers
    headers = [{'name': k, 'value': v} for k, v in msg.items()]

    # Walk MIME parts
    text_body = ''
    html_body = ''
    attachments = []

    for part in msg.walk():
        content_type = part.get_content_type()
        disposition = str(part.get('Content-Disposition', ''))

        if content_type == 'text/plain' and 'attachment' not in disposition:
            payload = part.get_content()
            if isinstance(payload, str):
                text_body += payload
        elif content_type == 'text/html' and 'attachment' not in disposition:
            payload = part.get_content()
            if isinstance(payload, str):
                html_body += payload
        elif part.get_filename() or 'attachment' in disposition:
            payload = part.get_payload(decode=True)
            attachments.append({
                'fileName': part.get_filename() or 'unknown',
                'contentType': content_type,
                'contentDisposition': disposition or 'N/A',
                'size': len(payload) if payload else 0,
                'contentId': part.get('Content-ID', ''),
            })

    # Extract links from HTML body
    links = []
    if html_body:
        links = re.findall(r'href=["\']([^"\']+)', html_body)

    # Generate warnings
    warnings = []
    from_header = msg.get('From', '')
    return_path = msg.get('Return-Path', '')
    if return_path and from_header:
        from_domain = re.search(r'@([\w.-]+)', from_header)
        return_domain = re.search(r'@([\w.-]+)', return_path)
        if from_domain and return_domain and from_domain.group(1).lower() != return_domain.group(1).lower():
            warnings.append(f'From domain ({from_domain.group(1)}) differs from Return-Path domain ({return_domain.group(1)})')

    if any('xn--' in link.lower() for link in links):
        warnings.append('Punycode (internationalized) domain detected in links')

    for link in links:
        if re.search(r'@', link) and not link.startswith('mailto:'):
            warnings.append(f'Suspicious @ symbol in URL: {link}')
            break

    return {
        'summary': summary,
        'headers': headers,
        'textBody': text_body,
        'htmlBody': html_body,
        'links': links,
        'attachments': attachments,
        'warnings': warnings,
    }


@bp.route('/')
def index():
    return render_template('inspector/inspector.html')


@bp.route('/api/emails')
def api_email_list():
    eml_files = _get_eml_files()
    emails = []
    for filepath in eml_files:
        try:
            emails.append(_parse_eml_summary(filepath))
        except Exception:
            continue
    return jsonify({
        'emails': emails,
        'samplesDirectory': EXAMPLES_DIR,
    })


@bp.route('/api/emails/<filename>')
def api_email_detail(filename):
    filepath = _find_eml_by_filename(filename)
    if not filepath:
        return jsonify({'error': 'Email not found'}), 404
    try:
        return jsonify(_parse_eml_detail(filepath))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
