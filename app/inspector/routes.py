import email
import email.policy
import re

from flask import current_app, jsonify, render_template

from app.inspector import bp

EML_PREFIX = 'eml-samples/'


def _s3_client():
    return current_app.s3_client


def _bucket():
    return current_app.config['S3_BUCKET']


def _get_eml_keys():
    """List all .eml object keys under the eml-samples/ prefix in S3."""
    try:
        resp = _s3_client().list_objects_v2(Bucket=_bucket(), Prefix=EML_PREFIX)
        keys = []
        for obj in resp.get('Contents', []):
            if obj['Key'].lower().endswith('.eml'):
                keys.append(obj['Key'])
        return sorted(keys)
    except Exception:
        return []


def _get_eml_body(key):
    """Download an EML file from S3 and return its bytes."""
    resp = _s3_client().get_object(Bucket=_bucket(), Key=key)
    return resp['Body'].read()


def _find_eml_key_by_filename(filename):
    """Find an .eml key by its basename, preventing path traversal."""
    import os
    basename = os.path.basename(filename)
    if basename != filename or '..' in filename:
        return None
    for key in _get_eml_keys():
        if key.split('/')[-1] == basename:
            return key
    return None


def _parse_eml_summary(key):
    """Parse an .eml file from S3 and return summary info."""
    body = _get_eml_body(key)
    msg = email.message_from_bytes(body, policy=email.policy.default)
    filename = key.split('/')[-1]
    return {
        'fileName': filename,
        'subject': msg.get('Subject', '(no subject)'),
        'from': msg.get('From', ''),
        'to': msg.get('To', ''),
        'date': msg.get('Date', ''),
    }


def _parse_eml_detail(key):
    """Parse an .eml file from S3 and return full details."""
    body = _get_eml_body(key)
    msg = email.message_from_bytes(body, policy=email.policy.default)

    filename = key.split('/')[-1]
    summary = {
        'fileName': filename,
        'subject': msg.get('Subject', '(no subject)'),
        'from': msg.get('From', ''),
        'to': msg.get('To', ''),
        'date': msg.get('Date', ''),
    }

    headers = [{'name': k, 'value': v} for k, v in msg.items()]

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

    links = []
    if html_body:
        links = re.findall(r'href=["\']([^"\']+)', html_body)

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
    eml_keys = _get_eml_keys()
    emails = []
    for key in eml_keys:
        try:
            emails.append(_parse_eml_summary(key))
        except Exception:
            continue
    return jsonify({
        'emails': emails,
        'samplesDirectory': f's3://{_bucket()}/{EML_PREFIX}',
    })


@bp.route('/api/emails/<filename>')
def api_email_detail(filename):
    key = _find_eml_key_by_filename(filename)
    if not key:
        return jsonify({'error': 'Email not found'}), 404
    try:
        return jsonify(_parse_eml_detail(key))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
