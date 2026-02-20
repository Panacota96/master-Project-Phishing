import email
import email.policy
import json
import random
import re

from flask import current_app, jsonify, render_template, request, session
from flask_login import current_user, login_required

from app.inspector import bp
from app.inspector.answer_key import ANSWER_KEY
from app.models import (
    create_inspector_attempt_anonymous,
    get_user_inspector_state,
    update_user_inspector_state,
)

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


def _get_or_create_email_pool():
    """Return a stable per-session list of email filenames (max 8)."""
    eml_keys = _get_eml_keys()
    key_map = {key.split('/')[-1]: key for key in eml_keys}

    pool = session.get('inspector_email_pool') or []
    if pool and all(name in key_map for name in pool):
        return pool, key_map

    filenames = [name for name in key_map.keys() if name in ANSWER_KEY]
    if not filenames:
        session['inspector_email_pool'] = []
        return [], key_map

    spam_files = [name for name in filenames if ANSWER_KEY.get(name, {}).get('classification') == 'Spam']
    phishing_files = [name for name in filenames if name not in spam_files]

    spam_max = min(3, len(spam_files))
    pool_size = min(8, len(filenames), len(phishing_files) + spam_max)

    spam_min = 1 if spam_files and pool_size > 0 else 0
    max_spam_allowed = min(spam_max, pool_size)
    min_spam_required = max(spam_min, pool_size - len(phishing_files))

    if min_spam_required > max_spam_allowed:
        spam_count = max_spam_allowed
    else:
        spam_count = random.randint(min_spam_required, max_spam_allowed)

    phishing_count = max(pool_size - spam_count, 0)
    chosen_spam = random.sample(spam_files, spam_count) if spam_count else []
    chosen_phishing = random.sample(phishing_files, phishing_count) if phishing_count else []
    pool = chosen_spam + chosen_phishing
    random.shuffle(pool)
    session['inspector_email_pool'] = pool
    return pool, key_map


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


def _try_parse_json_eml(body):
    """Return parsed JSON if body contains a JSON-formatted EML."""
    try:
        text = body.decode('utf-8', errors='ignore').lstrip()
    except Exception:
        return None
    if not text.startswith('{'):
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _clean_placeholders(text):
    """Replace common phishing template placeholders with generic values."""
    if not text:
        return text
    
    replacements = {
        # GoPhish / Template style
        r'\{\{\.FirstName\}\}': 'Valued',
        r'\{\{\.LastName\}\}': 'Customer',
        r'\{\{\.Email\}\}': 'user@example.com',
        r'\{\{\.URL\}\}': 'https://example.com/secure-redirect-gateway',
        r'\{\{\.TrackingURL\}\}': 'https://example.com/pixel-tracker',
        
        # Generic bracket style
        r'\[First Name\]': 'Customer',
        r'\[Last Name\]': 'Member',
        r'\[Company Name\]': 'Our Company',
        
        # Python/Jinja style
        r'\{\{first_name\}\}': 'Valued',
        r'\{\{last_name\}\}': 'Customer',
        r'\{\{company_name\}\}': 'Our Company',
        r'\{\{email\}\}': 'user@example.com',
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _parse_eml_summary(key):
    """Parse an .eml file from S3 and return summary info."""
    body = _get_eml_body(key)
    json_data = _try_parse_json_eml(body)
    filename = key.split('/')[-1]
    if json_data:
        summary = json_data.get('summary', {}) or {}
        return {
            'fileName': summary.get('fileName') or filename,
            'subject': _clean_placeholders(summary.get('subject', '(no subject)')),
            'from': _clean_placeholders(summary.get('from', '')),
            'to': _clean_placeholders(summary.get('to', '')),
            'date': summary.get('date', ''),
        }
    msg = email.message_from_bytes(body, policy=email.policy.default)
    return {
        'fileName': filename,
        'subject': _clean_placeholders(msg.get('Subject', '(no subject)')),
        'from': _clean_placeholders(msg.get('From', '')),
        'to': _clean_placeholders(msg.get('To', '')),
        'date': msg.get('Date', ''),
    }


def _parse_eml_detail(key):
    """Parse an .eml file from S3 and return full details."""
    body = _get_eml_body(key)
    filename = key.split('/')[-1]
    json_data = _try_parse_json_eml(body)
    if json_data:
        summary = json_data.get('summary', {}) or {}
        summary_payload = {
            'fileName': summary.get('fileName') or filename,
            'subject': _clean_placeholders(summary.get('subject', '(no subject)')),
            'from': _clean_placeholders(summary.get('from', '')),
            'to': _clean_placeholders(summary.get('to', '')),
            'date': summary.get('date', ''),
        }
        headers = json_data.get('headers', []) or []
        text_body = _clean_placeholders(json_data.get('textBody', '') or '')
        html_body = _clean_placeholders(json_data.get('htmlBody', '') or '')
        attachments = json_data.get('attachments', []) or []
        links = json_data.get('links', []) or []
        # Re-clean links in case they were placeholders in JSON
        links = [_clean_placeholders(link) for link in links]
        warnings = list(json_data.get('warnings', []) or [])
    else:
        msg = email.message_from_bytes(body, policy=email.policy.default)
        summary_payload = {
            'fileName': filename,
            'subject': _clean_placeholders(msg.get('Subject', '(no subject)')),
            'from': _clean_placeholders(msg.get('From', '')),
            'to': _clean_placeholders(msg.get('To', '')),
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

        text_body = _clean_placeholders(text_body)
        html_body = _clean_placeholders(html_body)

        links = []
        if html_body:
            links = re.findall(r'href=["\']([^"\']+)', html_body)
            # Clean extracted links (placeholder URLs)
            links = [_clean_placeholders(link) for link in links]

        warnings = []
        from_header = msg.get('From', '')
        return_path = msg.get('Return-Path', '')
        if return_path and from_header:
            from_domain = re.search(r'@([\w.-]+)', from_header)
            return_domain = re.search(r'@([\w.-]+)', return_path)
            if (
                from_domain
                and return_domain
                and from_domain.group(1).lower() != return_domain.group(1).lower()
            ):
                warnings.append(
                    (
                        f'From domain ({from_domain.group(1)}) differs from Return-Path domain '
                        f'({return_domain.group(1)})'
                    )
                )

    if current_user.is_admin and any('xn--' in link.lower() for link in links):
        warnings.append('Punycode (internationalized) domain detected in links')

    for link in links:
        if re.search(r'@', link) and not link.startswith('mailto:'):
            warnings.append(f'Suspicious @ symbol in URL: {link}')
            break

    return {
        'summary': summary_payload,
        'headers': headers,
        'textBody': text_body,
        'htmlBody': html_body,
        'links': links,
        'attachments': attachments,
        'warnings': warnings,
    }


@bp.route('/')
@login_required
def index():
    state = get_user_inspector_state(current_user.username)
    if state['locked']:
        return render_template('inspector/locked.html')
    return render_template('inspector/inspector.html')


@bp.route('/api/emails')
@login_required
def api_email_list():
    state = get_user_inspector_state(current_user.username)
    if state['locked']:
        return jsonify({'error': 'Inspector access is locked. Please return to main.'}), 403
    pool, key_map = _get_or_create_email_pool()
    emails = []
    for filename in pool:
        key = key_map.get(filename)
        if not key:
            continue
        try:
            emails.append(_parse_eml_summary(key))
        except Exception:
            continue
    return jsonify({
        'emails': emails,
        'samplesDirectory': f's3://{_bucket()}/{EML_PREFIX}',
    })


@bp.route('/api/emails/<filename>')
@login_required
def api_email_detail(filename):
    state = get_user_inspector_state(current_user.username)
    if state['locked']:
        return jsonify({'error': 'Inspector access is locked. Please return to main.'}), 403
    pool, _ = _get_or_create_email_pool()
    if filename not in pool:
        return jsonify({'error': 'Email not found'}), 404
    key = _find_eml_key_by_filename(filename)
    if not key:
        return jsonify({'error': 'Email not found'}), 404
    try:
        return jsonify(_parse_eml_detail(key))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/submit', methods=['POST'])
@login_required
def api_submit():
    data = request.get_json(silent=True) or {}
    filename = data.get('fileName')
    classification = data.get('classification')
    selected_signals = data.get('signals', [])

    if not filename:
        return jsonify({'error': 'Missing email filename.'}), 400

    state = get_user_inspector_state(current_user.username)
    if state['locked']:
        return jsonify({'error': 'Inspector access is locked. Please return to main.'}), 403

    pool, _ = _get_or_create_email_pool()
    if filename not in pool:
        return jsonify({'error': 'Email not found'}), 404

    submitted = state['submitted']
    if filename in submitted:
        return jsonify({'error': 'Answer already submitted for this email.'}), 409

    requirement = ANSWER_KEY.get(filename)
    if not requirement:
        return jsonify({'error': 'No answer key defined for this email.'}), 400

    if classification not in ('Spam', 'Phishing'):
        return jsonify({'error': 'Select either Spam or Phishing.'}), 400

    if classification == 'Phishing':
        if len(selected_signals) != 3:
            return jsonify({'error': 'Select exactly three phishing signals.'}), 400
    else:
        if selected_signals:
            return jsonify({'error': 'Spam classifications should not include phishing signals.'}), 400

    expected_classification = requirement['classification']
    expected_signals = requirement.get('signals', [])

    def normalize(value):
        return ''.join(ch for ch in (value or '').lower() if ch.isalnum())

    normalized_selected = [normalize(s) for s in selected_signals]
    normalized_expected = [normalize(s) for s in expected_signals]

    selected_set = set(normalized_selected)
    expected_set = set(normalized_expected)

    is_correct = False
    if classification == expected_classification:
        if classification == 'Spam':
            is_correct = True
        else:
            is_correct = selected_set == expected_set and len(selected_set) == len(expected_set)

    create_inspector_attempt_anonymous(
        email_file=filename,
        classification=classification,
        selected_signals=normalized_selected,
        expected_classification=expected_classification,
        expected_signals=normalized_expected,
        is_correct=is_correct,
        class_name=current_user.class_name,
        academic_year=current_user.academic_year,
        major=current_user.major,
    )

    submitted = submitted + [filename]
    target_count = len(pool) or 8
    completed = len(submitted) >= target_count
    update_user_inspector_state(
        current_user.username,
        submitted=submitted,
        locked=completed,
    )
    if completed:
        session.pop('inspector_email_pool', None)

    return jsonify({
        'success': True,
        'message': 'Answer saved.',
        'completed': completed,
    })
