import email
import email.policy
import json
import random
import re

from flask import current_app, jsonify, render_template, request, session
from flask_login import current_user, login_required

from app.inspector import bp
from app.models import (
    create_inspector_attempt_anonymous,
    get_effective_answer_key,
    get_inspector_config_for_cohort,
    get_user_inspector_state,
    update_user_inspector_state,
)

EML_PREFIX = 'eml-samples/'


def _s3_client():
    return current_app.s3_client


def _bucket():
    return current_app.config['S3_BUCKET']


def _get_eml_keys():
    """List all .eml/.json object keys under the eml-samples/ prefix in S3."""
    try:
        resp = _s3_client().list_objects_v2(Bucket=_bucket(), Prefix=EML_PREFIX)
        keys = []
        for obj in resp.get('Contents', []):
            key_lower = obj['Key'].lower()
            if key_lower.endswith('.eml') or key_lower.endswith('.json'):
                keys.append(obj['Key'])
        return sorted(keys)
    except Exception:
        return []


def _get_or_create_email_pool():
    """Return a stable per-session list of email filenames (max configurable)."""
    eml_keys = _get_eml_keys()
    key_map = {key.split('/')[-1]: key for key in eml_keys}

    pool = session.get('inspector_email_pool') or []
    if pool and all(name in key_map for name in pool):
        return pool, key_map

    cohort_config = get_inspector_config_for_cohort(
        getattr(current_user, 'class_name', 'unknown'),
        getattr(current_user, 'academic_year', 'unknown'),
        getattr(current_user, 'major', 'unknown'),
        getattr(current_user, 'facility', 'unknown'),
        getattr(current_user, 'group', 'default'),
    )

    answer_key = get_effective_answer_key()
    filenames = [name for name in key_map.keys() if name in answer_key]

    targets = cohort_config.get('targets') or []
    if targets:
        filenames = [name for name in filenames if name in targets]

    if not filenames:
        session['inspector_email_pool'] = []
        return [], key_map

    spam_files = [name for name in filenames if answer_key.get(name, {}).get('classification') == 'Spam']
    phishing_files = [name for name in filenames if name not in spam_files]

    max_spam_allowed = min(int(cohort_config.get('max_spam', 3)), len(spam_files))
    pool_size = min(
        int(cohort_config.get('pool_size', 8)),
        len(filenames),
        len(phishing_files) + max_spam_allowed,
    )
    if pool_size <= 0:
        pool_size = min(8, len(filenames))

    spam_min = 1 if spam_files and pool_size > 0 else 0
    spam_ratio = cohort_config.get('spam_ratio', 0.35)
    target_spam = int(round(pool_size * spam_ratio))
    min_spam_required = max(spam_min, pool_size - len(phishing_files), target_spam)

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


def _fix_duplicate_content_type(body: bytes) -> bytes:
    """Remove all but the last top-level Content-Type header.

    Fixes EML files that have a spurious 'Content-Type: text/html' header
    followed by the correct 'Content-Type: multipart/alternative' header.
    Without this, Python's email module picks the first Content-Type and treats
    the whole message as text/html, returning raw MIME boundary text as the body.
    """
    try:
        text = body.decode('utf-8', errors='replace')
    except Exception:
        return body

    lines = text.splitlines(keepends=True)
    sep_idx = next(
        (i for i, l in enumerate(lines) if l in ('\r\n', '\n', '\r')), None
    )
    if sep_idx is None:
        return body

    header_lines = lines[:sep_idx]
    ct_indices = [i for i, l in enumerate(header_lines)
                  if l.lower().startswith('content-type:')]

    if len(ct_indices) <= 1:
        return body

    to_remove = set(ct_indices[:-1])
    fixed = ''.join(l for i, l in enumerate(header_lines) if i not in to_remove)
    fixed += ''.join(lines[sep_idx:])
    return fixed.encode('utf-8', errors='replace')


def _clean_placeholders(text):
    """Replace common phishing template placeholders with generic values."""
    if not text:
        return text

    replacements = {
        # GoPhish / Template style — sliced variants first (e.g. {{.FirstName[:1]}})
        r'\{\{\.FirstName\[.*?\]\}\}': 'C',
        r'\{\{\.LastName\[.*?\]\}\}': 'M',
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
        body = _fix_duplicate_content_type(body)
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
    if state['locked'] and not current_user.is_admin:
        return render_template('inspector/locked.html')
    return render_template('inspector/inspector.html')


@bp.route('/api/emails')
@login_required
def api_email_list():
    state = get_user_inspector_state(current_user.username)
    if state['locked'] and not current_user.is_admin:
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
    if state['locked'] and not current_user.is_admin:
        return jsonify({'error': 'Inspector access is locked. Please return to main.'}), 403
    pool, _ = _get_or_create_email_pool()
    if filename not in pool and not current_user.is_admin:
        return jsonify({'error': 'Email not found'}), 404
    key = _find_eml_key_by_filename(filename)
    if not key:
        return jsonify({'error': 'Email not found'}), 404
    try:
        detail = _parse_eml_detail(key)
        answer_key = get_effective_answer_key()
        requirement = answer_key.get(filename, {})
        if requirement.get('classification') == 'Phishing':
            detail['requiredSignals'] = len(requirement.get('signals', []))
        else:
            detail['requiredSignals'] = 0
        return jsonify(detail)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/submit', methods=['POST'])
@login_required
def api_submit():
    data = request.get_json(silent=True) or {}
    filename = data.get('fileName')
    classification = data.get('classification')
    selected_signals = data.get('signals', [])
    explanation_rating = data.get('explanationRating') or data.get('explanation_rating')

    if not filename:
        return jsonify({'error': 'Missing email filename.'}), 400

    state = get_user_inspector_state(current_user.username)
    if state['locked'] and not current_user.is_admin:
        return jsonify({'error': 'Inspector access is locked. Please return to main.'}), 403

    pool, _ = _get_or_create_email_pool()
    if filename not in pool:
        return jsonify({'error': 'Email not found'}), 404

    submitted = state['submitted']
    if filename in submitted:
        return jsonify({'error': 'Answer already submitted for this email.'}), 409

    requirement = get_effective_answer_key().get(filename)
    if not requirement:
        return jsonify({'error': 'No answer key defined for this email.'}), 400

    if classification not in ('Spam', 'Phishing'):
        return jsonify({'error': 'Select either Spam or Phishing.'}), 400

    if classification == 'Phishing':
        expected_count = len(requirement.get('signals', []))
        if len(selected_signals) != expected_count:
            return jsonify({'error': f'Select exactly {expected_count} phishing signal(s).'}), 400
    else:
        if selected_signals:
            return jsonify({'error': 'Spam classifications should not include phishing signals.'}), 400

    rating_value = None
    if explanation_rating not in (None, ''):
        try:
            rating_value = int(explanation_rating)
        except (TypeError, ValueError):
            return jsonify({'error': 'Explanation rating must be a number between 1 and 5.'}), 400
        if rating_value < 1 or rating_value > 5:
            return jsonify({'error': 'Explanation rating must be between 1 and 5.'}), 400

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
        facility=getattr(current_user, 'facility', 'unknown'),
        explanation_rating=rating_value,
    )

    submitted = submitted + [filename]
    target_count = len(pool) or 8
    completed = len(submitted) >= target_count

    # For admins, we record progress but don't set the permanent lock
    new_lock_state = completed if not current_user.is_admin else False

    update_user_inspector_state(
        current_user.username,
        submitted=submitted,
        locked=new_lock_state,
    )

    # Don't clear pool for admins so they can continue testing
    if completed and not current_user.is_admin:
        session.pop('inspector_email_pool', None)

    return jsonify({
        'success': True,
        'message': 'Answer saved.',
        'completed': completed,
        'explanation': requirement.get('explanation', 'No detailed explanation available for this sample.')
    })
