import email
import email.policy
import re

from flask import current_app, jsonify, render_template, request
from flask_login import current_user, login_required

from app.inspector import bp
from app.inspector.answer_key import ANSWER_KEY
from app.models import create_inspector_attempt

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
@login_required
def index():
    return render_template('inspector/inspector.html')


@bp.route('/api/emails')
@login_required
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
@login_required
def api_email_detail(filename):
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

    correct_signals = [s for s in normalized_selected if s in expected_set]
    incorrect_signals = [s for s in normalized_selected if s not in expected_set]
    missing_signals = [s for s in normalized_expected if s not in selected_set]

    is_correct = False
    message = ''
    if classification != expected_classification:
        message = f'This email is expected to be {expected_classification.lower()}.'
    elif classification == 'Spam':
        is_correct = True
        message = 'Correct! This email is classified as spam.'
    else:
        if incorrect_signals or missing_signals or len(selected_set) != len(expected_set):
            message = 'Classification incorrect. Review the selected phishing signals.'
        else:
            is_correct = True
            message = f'Correct! Flag: {requirement.get("flag", "")}'.strip()

    create_inspector_attempt(
        username=current_user.username,
        group=current_user.group,
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

    return jsonify({
        'success': is_correct,
        'message': message,
        'correct_signals': correct_signals,
        'incorrect_signals': incorrect_signals,
        'missing_signals': missing_signals,
    })
