import csv
import io
import json
import os
import time
from uuid import uuid4
from datetime import datetime, timezone

import requests

from flask import (
    Response,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    stream_with_context,
    url_for,
)
from flask_login import current_user, login_required

from app.dashboard import bp
from app.dashboard.forms import AdminSetPasswordForm
from app.models import (
    count_users,
    create_bug_report,
    create_user,
    delete_answer_key_override,
    delete_user,
    get_distinct_cohorts,
    get_distinct_facilities,
    get_effective_answer_key,
    get_quiz,
    get_user,
    get_user_by_email,
    create_campaign,
    list_campaigns as list_campaigns_db,
    get_threat_cache,
    list_all_users,
    list_all_attempts,
    list_attempts_by_quiz,
    list_bug_reports,
    list_inspector_attempts_anonymous,
    list_quizzes,
    find_users_by_filters,
    record_campaign_event,
    reset_user_inspector_state,
    reset_users_inspector_state,
    save_inspector_config_for_cohort,
    set_answer_key_override,
    set_threat_cache,
    update_campaign_status,
    update_user_password,
)

# Simple in-memory cache for threat feed
THREAT_CACHE = {
    'data': [],
    'timestamp': 0
}

CAMPAIGN_STORE = []


def _redis_client():
    return getattr(current_app, 'redis_client', None)


def _publish(channel, payload):
    client = _redis_client()
    if not client:
        return
    try:
        if isinstance(payload, str):
            client.publish(channel, payload)
        else:
            client.publish(channel, json.dumps(payload))
    except Exception:
        current_app.logger.warning('Redis publish failed on %s', channel)


def _load_cached_threats():
    # Prefer DynamoDB TTL cache when available
    cached = get_threat_cache()
    if cached:
        return cached
    now = time.time()
    if now - THREAT_CACHE['timestamp'] < current_app.config.get('THREAT_CACHE_TTL_SECONDS', 3600):
        return THREAT_CACHE['data']
    return []


def _save_cached_threats(data):
    THREAT_CACHE['data'] = data
    THREAT_CACHE['timestamp'] = time.time()
    set_threat_cache(data)


def _campaign_filters_from_request():
    filters = {
        'class_name': request.form.get('class_name', 'All'),
        'academic_year': request.form.get('academic_year', 'All'),
        'major': request.form.get('major', 'All'),
        'facility': request.form.get('facility', 'All'),
        'group': request.form.get('group', 'All'),
    }
    cohort = request.form.get('cohort', '')
    if cohort and all(v in ('', 'All') for v in filters.values()):
        parts = cohort.split('|')
        if len(parts) >= 4:
            filters.update({
                'class_name': parts[0] or 'All',
                'academic_year': parts[1] or 'All',
                'major': parts[2] or 'All',
                'facility': parts[3] or 'All',
            })
            if len(parts) >= 5:
                filters['group'] = parts[4] or 'All'
    return filters


@bp.route('/api/threat-feed')
@login_required
def api_threat_feed():
    """Fetch and defang real-time phishing URLs from OpenPhish."""
    if not current_user.is_admin:
        abort(403)

    if current_app.config.get('TESTING') or os.environ.get('DISABLE_THREAT_FEED_NETWORK'):
        sample = [{
            'target': 'Microsoft 365',
            'url': 'hxxps://login.microsoftonline.com.evil[.]com/verify',
            'raw_url': 'https://login.microsoftonline.com.evil.com/verify',
            'fetched_at': datetime.now(timezone.utc).isoformat(),
        }]
        _save_cached_threats(sample)
        return jsonify(sample)

    cached = _load_cached_threats()
    if cached:
        return jsonify(cached)

    try:
        # OpenPhish free feed provides raw URLs
        resp = requests.get('https://openphish.com/feed.txt', timeout=5)
        if resp.status_code == 200:
            urls = resp.text.splitlines()[:10]  # Top 10 recent
            defanged = []
            for u in urls:
                if not u.strip():
                    continue
                # Defang for safety
                safe_url = u.replace('http', 'hxxp').replace('.', '[.]')
                # Simple heuristic to guess target (very rough)
                target = "Unknown"
                if 'paypal' in u:
                    target = "PayPal"
                elif 'microsoft' in u or 'office365' in u:
                    target = "Microsoft"
                elif 'google' in u or 'gmail' in u:
                    target = "Google"
                elif 'amazon' in u:
                    target = "Amazon"
                elif 'apple' in u or 'icloud' in u:
                    target = "Apple"

                defanged.append({
                    'target': target,
                    'url': safe_url,
                    'raw_url': u,
                    'fetched_at': datetime.now(timezone.utc).isoformat(),
                })

            _save_cached_threats(defanged)
            return jsonify(defanged)

    except Exception as e:
        current_app.logger.error(f"Threat feed fetch failed: {e}")

    return jsonify([])  # Return empty list on failure


@bp.route('/api/threat-feed/promote', methods=['POST'])
@login_required
def promote_threat_to_inspector():
    """Promote a threat-feed URL into the inspector dataset as a JSON EML sample."""
    if not current_user.is_admin:
        abort(403)

    data = request.get_json(silent=True) or {}
    url = data.get('raw_url') or data.get('url', '')
    url = url.strip()
    target = data.get('target', 'Unknown')
    if not url:
        return jsonify({'error': 'url is required'}), 400

    filename = data.get('filename') or f"openphish-{int(time.time())}.json"
    if not filename.lower().endswith('.json'):
        filename = f"{filename}.json"

    summary = {
        'fileName': filename,
        'subject': f"Suspicious link reported: {target}",
        'from': 'threat-intel@openphish.example',
        'to': 'student@example.com',
        'date': datetime.now(timezone.utc).isoformat(),
    }
    body = {
        'summary': summary,
        'headers': [
            {'name': 'X-Imported-From', 'value': 'OpenPhish'},
            {'name': 'X-Target', 'value': target},
        ],
        'textBody': f"This synthetic training sample references {url}",
        'htmlBody': f"<p>This synthetic training sample references <strong>{url}</strong></p>",
        'attachments': [],
        'links': [url],
        'warnings': ['Imported from live threat feed; treat as phishing training material'],
    }

    try:
        s3_key = f"eml-samples/{filename}"
        current_app.s3_client.put_object(
            Bucket=current_app.config['S3_BUCKET'],
            Key=s3_key,
            Body=json.dumps(body).encode('utf-8'),
            ContentType='application/json',
        )
        # Default ground truth: phishing with common signals
        set_answer_key_override(
            filename,
            classification='Phishing',
            signals=['externaldomain', 'fakelogin', 'urgency'],
            explanation=f'Live threat imported from OpenPhish ({target}).',
        )
        return jsonify({'success': True, 'email_file': filename})
    except Exception:
        current_app.logger.exception('Failed to promote threat feed URL')
        return jsonify({'error': 'Failed to promote threat to inspector.'}), 500


@bp.route('/users')
@login_required
def list_users():
    if not current_user.is_admin:
        abort(403)
    users = list_all_users()
    set_password_form = AdminSetPasswordForm()
    return render_template('admin/users.html', users=users, set_password_form=set_password_form)


@bp.route('/users/delete/<username>', methods=['POST'])
@login_required
def remove_user(username):
    if not current_user.is_admin:
        abort(403)

    if username == current_user.username:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for('dashboard.list_users'))

    try:
        delete_user(username)
        flash(f"User {username} has been deleted.", "success")
    except Exception as e:
        current_app.logger.error(f"Failed to delete user {username}: {e}")
        flash("Failed to delete user.", "danger")

    return redirect(url_for('dashboard.list_users'))


@bp.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        abort(403)

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    class_name = request.form.get('class_name', 'unknown').strip() or 'unknown'
    academic_year = request.form.get('academic_year', 'unknown').strip() or 'unknown'
    major = request.form.get('major', 'unknown').strip() or 'unknown'
    facility = request.form.get('facility', 'unknown').strip() or 'unknown'
    group = request.form.get('group', 'default').strip() or 'default'

    if not username or not email or not password:
        flash('Username, email, and password are required.', 'danger')
        return redirect(url_for('dashboard.list_users'))

    if get_user(username):
        flash(f'Username "{username}" already exists.', 'danger')
        return redirect(url_for('dashboard.list_users'))

    if get_user_by_email(email):
        flash(f'Email "{email}" is already in use.', 'danger')
        return redirect(url_for('dashboard.list_users'))

    try:
        create_user(
            username=username,
            email=email,
            password=password,
            class_name=class_name,
            academic_year=academic_year,
            major=major,
            facility=facility,
            group=group,
        )
        flash(f'User "{username}" created successfully.', 'success')
    except Exception as e:
        current_app.logger.error(f'Failed to create user {username}: {e}')
        flash('Failed to create user.', 'danger')

    return redirect(url_for('dashboard.list_users'))


@bp.route('/users/<username>/set-password', methods=['POST'])
@login_required
def set_user_password(username):
    """Allow an admin to set a new password for any user."""
    if not current_user.is_admin:
        abort(403)

    target = get_user(username)
    if target is None:
        abort(404)

    form = AdminSetPasswordForm()
    if form.validate_on_submit():
        update_user_password(username, form.new_password.data)
        flash(f'Password updated for {username}.', 'success')
    else:
        for field_errors in form.errors.values():
            for err in field_errors:
                flash(err, 'danger')

    return redirect(url_for('dashboard.list_users'))


@bp.route('/bugs')
@login_required
def list_bugs():
    if not current_user.is_admin:
        abort(403)
    bugs = list_bug_reports()
    return render_template('admin/bugs.html', bugs=bugs)


@bp.route('/report-bug', methods=['POST'])
@login_required
def report_bug():
    description = request.form.get('description', '').strip()
    if not description:
        flash('Bug description cannot be empty.', 'danger')
        return redirect(request.referrer or url_for('quiz.quiz_list'))

    try:
        create_bug_report(
            username=current_user.username,
            description=description,
            page_url=request.referrer or 'Unknown'
        )
        flash('Bug reported successfully. Thank you!', 'success')
    except Exception as e:
        current_app.logger.error(f"Failed to report bug: {e}")
        flash('Failed to report bug. Please try again later.', 'danger')

    return redirect(request.referrer or url_for('quiz.quiz_list'))


@bp.route('/risk')
@login_required
def risk_dashboard():
    if not current_user.is_admin:
        abort(403)

    inspector_attempts = list_inspector_attempts_anonymous()
    quiz_attempts = list_all_attempts()

    # Risk Score Calculation (0-100, where 100 is high risk)
    # Factor 1: Signal Miss Rate (Students missing phishing indicators)
    # Factor 2: Quiz Failure Rate (Score < 70%)

    cohort_risk = {}  # {(class, year, major, facility): {signal_misses: 0, quiz_fails: 0, total_actions: 0}}

    for a in inspector_attempts:
        key = (
            a.get('class_name', 'unknown'),
            a.get('academic_year', 'unknown'),
            a.get('major', 'unknown'),
            a.get('facility', 'unknown'),
        )
        if key not in cohort_risk:
            cohort_risk[key] = {'signal_misses': 0, 'quiz_fails': 0, 'total_actions': 0}

        cohort_risk[key]['total_actions'] += 1
        if not a.get('is_correct'):
            cohort_risk[key]['signal_misses'] += 1

    for a in quiz_attempts:
        key = (
            a.get('class_name', 'unknown'),
            a.get('academic_year', 'unknown'),
            a.get('major', 'unknown'),
            a.get('facility', 'unknown'),
        )
        if key not in cohort_risk:
            cohort_risk[key] = {'signal_misses': 0, 'quiz_fails': 0, 'total_actions': 0}

        cohort_risk[key]['total_actions'] += 1
        if float(a.get('percentage', 0)) < 70:
            cohort_risk[key]['quiz_fails'] += 1

    risk_data = []
    for (c, y, m, f), stats in cohort_risk.items():
        if stats['total_actions'] > 0:
            # Risk = Average of (miss rate + fail rate)
            miss_rate = (stats['signal_misses'] / stats['total_actions']) * 100
            fail_rate = (stats['quiz_fails'] / stats['total_actions']) * 100
            risk_score = round((miss_rate + fail_rate) / 2, 1)

            risk_data.append({
                'class_name': c,
                'academic_year': y,
                'major': m,
                'facility': f,
                'risk_score': risk_score,
                'label': f"{c} | {y} | {m} | {f}",
                'level': 'High' if risk_score > 60 else 'Medium' if risk_score > 30 else 'Low'
            })

    risk_data.sort(key=lambda x: x['risk_score'], reverse=True)

    return render_template('admin/risk_dashboard.html', risk_data=risk_data)


@bp.route('/inspector/answer-key')
@login_required
def inspector_answer_key():
    if not current_user.is_admin:
        abort(403)

    from app.models import get_answer_key_overrides
    overrides = get_answer_key_overrides()
    effective = get_effective_answer_key()

    sorted_keys = sorted(effective.keys())
    items = []
    for filename in sorted_keys:
        entry = effective[filename]
        items.append({
            'filename': filename,
            'classification': entry['classification'],
            'signals': entry.get('signals', []),
            'explanation': entry.get('explanation', ''),
            'has_override': filename in overrides,
        })

    return render_template('admin/inspector_answer_key.html', items=items)


@bp.route('/inspector/answer-key/edit', methods=['POST'])
@login_required
def edit_answer_key():
    if not current_user.is_admin:
        abort(403)
    email_file = request.form.get('email_file', '').strip()
    classification = request.form.get('classification', '').strip()
    signals_raw = request.form.get('signals', '').strip()
    explanation = request.form.get('explanation', '').strip()

    if not email_file or classification not in ('Phishing', 'Spam'):
        return jsonify({'error': 'Invalid input.'}), 400

    signals = [s.strip() for s in signals_raw.split(',') if s.strip()] if signals_raw else []
    set_answer_key_override(email_file, classification, signals, explanation)
    return jsonify({'success': True})


@bp.route('/inspector/answer-key/reset', methods=['POST'])
@login_required
def reset_answer_key():
    if not current_user.is_admin:
        abort(403)
    email_file = request.form.get('email_file', '').strip()
    if not email_file:
        return jsonify({'error': 'email_file is required.'}), 400
    delete_answer_key_override(email_file)
    return jsonify({'success': True})


@bp.route('/inspector/config', methods=['POST'])
@login_required
def update_inspector_config():
    """Admin-only endpoint to tune inspector pool per cohort."""
    if not current_user.is_admin:
        abort(403)

    class_name = request.form.get('class_name', 'unknown').strip() or 'unknown'
    academic_year = request.form.get('academic_year', 'unknown').strip() or 'unknown'
    major = request.form.get('major', 'unknown').strip() or 'unknown'
    facility = request.form.get('facility', 'unknown').strip() or 'unknown'
    group = request.form.get('group', 'default').strip() or 'default'
    pool_size = request.form.get('pool_size') or current_app.config.get('INSPECTOR_POOL_SIZE_DEFAULT', 8)
    max_spam = request.form.get('max_spam') or current_app.config.get('INSPECTOR_MAX_SPAM_DEFAULT', 3)
    spam_ratio = request.form.get('spam_ratio') or current_app.config.get('INSPECTOR_SPAM_RATIO_DEFAULT', 0.35)
    targets_raw = request.form.get('targets', '')

    try:
        pool_size_int = max(1, int(pool_size))
        max_spam_int = max(0, int(max_spam))
        spam_ratio_f = max(0.0, min(1.0, float(spam_ratio)))
    except ValueError:
        return jsonify({'error': 'Invalid numeric value.'}), 400

    targets = [t.strip() for t in targets_raw.split(',') if t.strip()]

    config = save_inspector_config_for_cohort(
        class_name,
        academic_year,
        major,
        facility,
        group,
        {
            'pool_size': pool_size_int,
            'max_spam': max_spam_int,
            'spam_ratio': spam_ratio_f,
            'targets': targets,
        },
    )
    return jsonify({'success': True, 'config': config})


@bp.route('/api/campaigns', methods=['GET'])
@login_required
def list_campaigns():
    if not current_user.is_admin:
        abort(403)
    campaigns = list_campaigns_db()
    if not campaigns:
        campaigns = CAMPAIGN_STORE
    return jsonify({'campaigns': campaigns})


@bp.route('/campaigns/launch', methods=['POST'])
@login_required
def launch_campaign():
    if not current_user.is_admin:
        abort(403)

    filters = _campaign_filters_from_request()
    cohort_label = (
        f"{filters['class_name']}|{filters['academic_year']}|"
        f"{filters['major']}|{filters['facility']}|{filters['group']}"
    )

    campaign = create_campaign(cohort_label, filters, status='queued')
    if not campaign:
        campaign = {
            'campaign_id': str(uuid4()),
            'cohort': cohort_label,
            'filters': filters,
            'status': 'queued',
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        CAMPAIGN_STORE.insert(0, campaign)
        CAMPAIGN_STORE[:] = CAMPAIGN_STORE[:25]

    payload = {
        'campaign_id': campaign['campaign_id'],
        'filters': filters,
    }

    queue_url = current_app.config.get('SQS_CAMPAIGN_QUEUE_URL')
    try:
        if queue_url:
            current_app.sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(payload),
            )
            update_campaign_status(campaign['campaign_id'], 'queued')
            record_campaign_event(campaign['campaign_id'], 'queued', {'note': 'Queued via SQS'})
        elif current_app.config.get('CAMPAIGN_LAMBDA_ARN') and getattr(current_app, 'lambda_client', None):
            current_app.lambda_client.invoke(
                FunctionName=current_app.config['CAMPAIGN_LAMBDA_ARN'],
                InvocationType='Event',
                Payload=json.dumps(payload).encode('utf-8'),
            )
            update_campaign_status(campaign['campaign_id'], 'queued')
        else:
            update_campaign_status(campaign['campaign_id'], 'queued')
    except Exception:
        update_campaign_status(campaign['campaign_id'], 'failed')
        current_app.logger.exception('Failed to queue campaign')
        return jsonify({'error': 'Failed to queue campaign'}), 500

    _publish('campaign-events', {'type': 'queued', 'campaign_id': campaign['campaign_id']})
    return jsonify({'success': True, 'campaign': campaign})


@bp.route('/campaigns/validation-email', methods=['POST'])
@login_required
def send_validation_email():
    if not current_user.is_admin:
        abort(403)

    filters = _campaign_filters_from_request()
    template = current_app.config.get('VALIDATION_EMAIL_TEMPLATE')
    ses_from = current_app.config.get('SES_FROM_EMAIL')
    if not ses_from:
        return jsonify({'error': 'SES_FROM_EMAIL not configured.'}), 400

    users = find_users_by_filters(filters)
    if not users:
        return jsonify({'error': 'No matching users found for this cohort.'}), 404

    sent = 0
    for user in users:
        try:
            subject = 'Email validation'
            body_text = (
                f"Hello {user.username},\n\n"
                "This is a validation email to confirm delivery for the upcoming phishing simulation."
            )
            body_html = f"""
            <html><body>
            <p>Hello <strong>{user.username}</strong>,</p>
            <p>This is a validation email to confirm delivery for the upcoming phishing simulation.</p>
            </body></html>
            """
            current_app.ses_client.send_email(
                Source=ses_from,
                Destination={'ToAddresses': [user.email]},
                Message={
                    'Subject': {'Data': template or subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                        'Html': {'Data': body_html, 'Charset': 'UTF-8'},
                    },
                },
            )
            sent += 1
        except Exception:
            current_app.logger.exception('Failed to send validation email to %s', user.email)

    record_campaign_event('validation', 'validation', {'recipients': sent})
    _publish('campaign-events', {'type': 'validation', 'recipients': sent})
    return jsonify({'success': True, 'message': f'Validation email triggered for cohort; sent {sent} emails.'})


@bp.route('/animation')
@login_required
def animation():
    return render_template('dashboard/animation.html')


@bp.route('/')
@login_required
def index():
    if not current_user.is_admin:
        abort(403)

    total_users = count_users()
    attempts = list_all_attempts()
    total_attempts = len(attempts)

    # Average score
    if total_attempts > 0:
        avg_score = round(
            sum(float(a.get('percentage', 0)) for a in attempts) / total_attempts, 1
        )
    else:
        avg_score = 0

    # Completed vs pending
    completed_count = total_attempts
    pending_count = total_users - completed_count

    # Score distribution buckets: 0-20, 20-40, 40-60, 60-80, 80-100
    score_distribution = [0, 0, 0, 0, 0]
    for attempt in attempts:
        pct = float(attempt.get('percentage', 0))
        if pct < 20:
            score_distribution[0] += 1
        elif pct < 40:
            score_distribution[1] += 1
        elif pct < 60:
            score_distribution[2] += 1
        elif pct < 80:
            score_distribution[3] += 1
        else:
            score_distribution[4] += 1

    # Per-quiz stats
    quiz_stats = []
    quizzes = list_quizzes()
    for quiz in quizzes:
        quiz_attempts = list_attempts_by_quiz(quiz['quiz_id'])
        count = len(quiz_attempts)
        if count > 0:
            avg = round(sum(float(a.get('percentage', 0)) for a in quiz_attempts) / count, 1)
        else:
            avg = 0
        quiz_stats.append({'title': quiz['title'], 'count': count, 'avg': avg})

    # Cohort stats (class/year/major/facility)
    cohort_stats = {}
    for attempt in attempts:
        class_name = attempt.get('class_name', 'unknown')
        academic_year = attempt.get('academic_year', 'unknown')
        major = attempt.get('major', 'unknown')
        facility = attempt.get('facility', 'unknown')
        key = (class_name, academic_year, major, facility)
        if key not in cohort_stats:
            cohort_stats[key] = {'count': 0, 'total_pct': 0.0}
        cohort_stats[key]['count'] += 1
        cohort_stats[key]['total_pct'] += float(attempt.get('percentage', 0))

    group_stats = []
    for (class_name, academic_year, major, facility), stats in cohort_stats.items():
        count = stats['count']
        avg = round(stats['total_pct'] / count, 1) if count > 0 else 0
        group_stats.append({
            'class_name': class_name,
            'academic_year': academic_year,
            'major': major,
            'facility': facility,
            'count': count,
            'avg': avg,
            'label': f'{class_name} | {academic_year} | {major} | {facility}',
        })

    # Inspector analytics
    inspector_attempts = list_inspector_attempts_anonymous()
    inspector_total = len(inspector_attempts)
    inspector_correct = sum(1 for a in inspector_attempts if a.get('is_correct'))
    inspector_phishing = sum(1 for a in inspector_attempts if a.get('classification') == 'Phishing')
    inspector_spam = sum(1 for a in inspector_attempts if a.get('classification') == 'Spam')
    rating_total = 0
    rating_count = 0

    # Signal Accuracy Stats
    signal_stats = {}  # {signal_alias: {expected: 0, identified: 0}}
    for attempt in inspector_attempts:
        expected = attempt.get('expected_signals', [])
        selected = attempt.get('selected_signals', [])
        rating_val = attempt.get('explanation_rating')
        if rating_val is not None:
            try:
                rating_total += float(rating_val)
                rating_count += 1
            except (TypeError, ValueError):
                pass
        for sig in expected:
            if sig not in signal_stats:
                signal_stats[sig] = {'expected': 0, 'identified': 0}
            signal_stats[sig]['expected'] += 1
            if sig in selected:
                signal_stats[sig]['identified'] += 1

    signal_accuracy = []
    for sig, stats in signal_stats.items():
        rate = round((stats['identified'] / stats['expected'] * 100), 1) if stats['expected'] > 0 else 0
        signal_accuracy.append({'signal': sig, 'rate': rate})
    signal_accuracy.sort(key=lambda x: x['rate'], reverse=True)

    per_email = {}
    for attempt in inspector_attempts:
        email_file = attempt.get('email_file', 'unknown')
        if email_file not in per_email:
            per_email[email_file] = {'email_file': email_file, 'count': 0, 'correct': 0}
        per_email[email_file]['count'] += 1
        if attempt.get('is_correct'):
            per_email[email_file]['correct'] += 1
    for stats in per_email.values():
        stats['incorrect'] = stats['count'] - stats['correct']

    inspector_per_email = sorted(
        per_email.values(),
        key=lambda item: item['count'],
        reverse=True,
    )
    inspector_avg_rating = round(rating_total / rating_count, 1) if rating_count else None
    inspector_progress_map = {}
    for attempt in inspector_attempts:
        key = (
            attempt.get('class_name', 'unknown'),
            attempt.get('academic_year', 'unknown'),
            attempt.get('major', 'unknown'),
            attempt.get('facility', 'unknown'),
        )
        if key not in inspector_progress_map:
            inspector_progress_map[key] = {'attempts': 0, 'correct': 0}
        inspector_progress_map[key]['attempts'] += 1
        if attempt.get('is_correct'):
            inspector_progress_map[key]['correct'] += 1
    inspector_progress_rows = []
    for (class_name, academic_year, major, facility), stats in inspector_progress_map.items():
        inspector_progress_rows.append({
            'class_name': class_name,
            'academic_year': academic_year,
            'major': major,
            'facility': facility,
            'attempts': stats['attempts'],
            'correct': stats['correct'],
        })

    return render_template(
        'dashboard/dashboard.html',
        total_users=total_users,
        total_attempts=total_attempts,
        avg_score=avg_score,
        completed_count=completed_count,
        pending_count=pending_count,
        score_distribution=score_distribution,
        quiz_stats=quiz_stats,
        group_stats=group_stats,
        inspector_total=inspector_total,
        inspector_correct=inspector_correct,
        inspector_phishing=inspector_phishing,
        inspector_spam=inspector_spam,
        inspector_avg_rating=inspector_avg_rating,
        inspector_progress_rows=inspector_progress_rows,
        inspector_recent=[],
        inspector_per_email=inspector_per_email,
        signal_accuracy=signal_accuracy,
    )


def _build_live_stats():
    total_users = count_users()
    attempts = list_all_attempts()
    total_attempts = len(attempts)

    if total_attempts > 0:
        avg_score = round(
            sum(float(a.get('percentage', 0)) for a in attempts) / total_attempts, 1
        )
    else:
        avg_score = 0

    completed_count = total_attempts
    pending_count = total_users - completed_count

    per_group = {}
    for attempt in attempts:
        class_name = attempt.get('class_name', 'unknown')
        academic_year = attempt.get('academic_year', 'unknown')
        major = attempt.get('major', 'unknown')
        key = f'{class_name} | {academic_year} | {major}'
        if key not in per_group:
            per_group[key] = {'count': 0, 'total_pct': 0.0}
        per_group[key]['count'] += 1
        per_group[key]['total_pct'] += float(attempt.get('percentage', 0))
    for stats in per_group.values():
        count = stats['count']
        stats['avg'] = round(stats['total_pct'] / count, 1) if count > 0 else 0

    inspector_attempts = list_inspector_attempts_anonymous()
    inspector_progress = {}
    rating_total = 0
    rating_count = 0
    for attempt in inspector_attempts:
        key = (
            attempt.get('class_name', 'unknown'),
            attempt.get('academic_year', 'unknown'),
            attempt.get('major', 'unknown'),
            attempt.get('facility', 'unknown'),
        )
        if key not in inspector_progress:
            inspector_progress[key] = {'attempts': 0, 'correct': 0}
        inspector_progress[key]['attempts'] += 1
        if attempt.get('is_correct'):
            inspector_progress[key]['correct'] += 1
        rating_val = attempt.get('explanation_rating')
        if rating_val is not None:
            try:
                rating_total += float(rating_val)
                rating_count += 1
            except (TypeError, ValueError):
                continue

    inspector_rows = []
    for (class_name, academic_year, major, facility), stats in inspector_progress.items():
        inspector_rows.append({
            'class_name': class_name,
            'academic_year': academic_year,
            'major': major,
            'facility': facility,
            'attempts': stats['attempts'],
            'correct': stats['correct'],
        })

    avg_rating = round(rating_total / rating_count, 1) if rating_count else None

    return {
        'total_users': total_users,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'avg_score': avg_score,
        'per_group': per_group,
        'inspector_progress': inspector_rows,
        'avg_explanation_rating': avg_rating,
    }


@bp.route('/api/stats/stream')
@login_required
def api_stats_stream():
    """Server-sent events stream for real-time dashboard updates."""
    if not current_user.is_admin:
        abort(403)

    def event_stream():
        client = _redis_client()
        if client:
            pubsub = client.pubsub()
            pubsub.subscribe('dashboard:stats')
            initial = json.dumps(_build_live_stats())
            _publish('dashboard:stats', initial)
            yield f"data: {initial}\n\n"
            try:
                for message in pubsub.listen():
                    if message['type'] != 'message':
                        continue
                    data = message['data']
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    yield f"data: {data}\n\n"
            finally:
                pubsub.close()
        else:
            while True:
                payload = json.dumps(_build_live_stats())
                yield f"data: {payload}\n\n"
                time.sleep(5)

    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache'},
    )


@bp.route('/api/stats')
@login_required
def api_stats():
    """Live statistics endpoint — polled by the dashboard every 30 seconds."""
    if not current_user.is_admin:
        abort(403)
    stats = _build_live_stats()
    _publish('dashboard:stats', stats)
    return jsonify(stats)


@bp.route('/reports')
@login_required
def reports():
    if not current_user.is_admin:
        abort(403)
    cohorts = get_distinct_cohorts()
    classes = sorted({c[0] for c in cohorts})
    years = sorted({c[1] for c in cohorts})
    majors = sorted({c[2] for c in cohorts})
    facilities = get_distinct_facilities()
    return render_template(
        'admin/reports.html',
        classes=classes,
        years=years,
        majors=majors,
        facilities=facilities,
    )


@bp.route('/inspector')
@login_required
def inspector_analytics():
    if not current_user.is_admin:
        abort(403)

    attempts = list_inspector_attempts_anonymous()
    attempts_sorted = attempts

    classes = sorted({a.get('class_name', 'unknown') for a in attempts_sorted})
    years = sorted({a.get('academic_year', 'unknown') for a in attempts_sorted})
    majors = sorted({a.get('major', 'unknown') for a in attempts_sorted})
    emails = sorted({a.get('email_file', '') for a in attempts_sorted if a.get('email_file')})
    facilities = get_distinct_facilities()

    selected_class = request.args.get('class_name', '')
    selected_year = request.args.get('academic_year', '')
    selected_major = request.args.get('major', '')
    selected_email = request.args.get('email', '')
    selected_facility = request.args.get('facility', '')
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    sort_by = request.args.get('sort_by', 'attempts')
    sort_order = request.args.get('sort_order', 'desc')
    page = request.args.get('page', '1')

    filtered = attempts_sorted
    if selected_class:
        filtered = [a for a in filtered if a.get('class_name', 'unknown') == selected_class]
    if selected_year:
        filtered = [a for a in filtered if a.get('academic_year', 'unknown') == selected_year]
    if selected_major:
        filtered = [a for a in filtered if a.get('major', 'unknown') == selected_major]
    if selected_email:
        filtered = [a for a in filtered if a.get('email_file') == selected_email]
    if selected_facility:
        filtered = [a for a in filtered if a.get('facility', 'unknown') == selected_facility]

    if date_from or date_to:
        def parse_date(value, end_of_day=False):
            if not value:
                return None
            if end_of_day:
                return datetime.fromisoformat(f'{value}T23:59:59+00:00')
            return datetime.fromisoformat(f'{value}T00:00:00+00:00')

        start_dt = parse_date(date_from, end_of_day=False)
        end_dt = parse_date(date_to, end_of_day=True)

        def in_range(item):
            submitted_at = item.get('submitted_at')
            if not submitted_at:
                return False
            try:
                submitted_dt = datetime.fromisoformat(submitted_at)
            except ValueError:
                return False
            if start_dt and submitted_dt < start_dt:
                return False
            if end_dt and submitted_dt > end_dt:
                return False
            return True

        filtered = [a for a in filtered if in_range(a)]

    aggregated = {}
    for a in filtered:
        key = (
            a.get('class_name', 'unknown'),
            a.get('academic_year', 'unknown'),
            a.get('major', 'unknown'),
            a.get('facility', 'unknown'),
        )
        if key not in aggregated:
            aggregated[key] = {'attempts': 0, 'correct': 0, 'phishing': 0, 'spam': 0}
        aggregated[key]['attempts'] += 1
        if a.get('is_correct'):
            aggregated[key]['correct'] += 1
        if a.get('classification') == 'Phishing':
            aggregated[key]['phishing'] += 1
        if a.get('classification') == 'Spam':
            aggregated[key]['spam'] += 1

    aggregated_rows = []
    for (class_name, academic_year, major, facility), stats in aggregated.items():
        attempts_count = stats['attempts']
        correct_pct = round((stats['correct'] / attempts_count * 100), 1) if attempts_count > 0 else 0
        aggregated_rows.append({
            'class_name': class_name,
            'academic_year': academic_year,
            'major': major,
            'facility': facility,
            'attempts': attempts_count,
            'correct': stats['correct'],
            'correct_pct': correct_pct,
            'phishing': stats['phishing'],
            'spam': stats['spam'],
        })

    allowed_sort = {
        'class_name': lambda a: a.get('class_name', ''),
        'academic_year': lambda a: a.get('academic_year', ''),
        'major': lambda a: a.get('major', ''),
        'facility': lambda a: a.get('facility', ''),
        'attempts': lambda a: a.get('attempts', 0),
        'correct_pct': lambda a: a.get('correct_pct', 0),
        'phishing': lambda a: a.get('phishing', 0),
        'spam': lambda a: a.get('spam', 0),
    }
    sort_key = allowed_sort.get(sort_by, allowed_sort['attempts'])
    reverse = sort_order != 'asc'
    aggregated_rows = sorted(aggregated_rows, key=sort_key, reverse=reverse)

    try:
        page_num = max(int(page), 1)
    except ValueError:
        page_num = 1
    per_page = 50
    total_attempts = sum(row['attempts'] for row in aggregated_rows)
    total_rows = len(aggregated_rows)
    total_pages = max((total_rows + per_page - 1) // per_page, 1)
    if page_num > total_pages:
        page_num = total_pages
    start = (page_num - 1) * per_page
    end = start + per_page
    paged_attempts = aggregated_rows[start:end]

    from urllib.parse import urlencode
    base_params = request.args.to_dict()
    prev_url = None
    next_url = None
    if page_num > 1:
        base_params['page'] = str(page_num - 1)
        prev_url = f"?{urlencode(base_params)}"
    if page_num < total_pages:
        base_params['page'] = str(page_num + 1)
        next_url = f"?{urlencode(base_params)}"

    correct_attempts = sum(row['correct'] for row in aggregated_rows)
    phishing_attempts = sum(row['phishing'] for row in aggregated_rows)
    spam_attempts = sum(row['spam'] for row in aggregated_rows)

    return render_template(
        'admin/inspector.html',
        attempts=paged_attempts,
        total_attempts=total_attempts,
        correct_attempts=correct_attempts,
        phishing_attempts=phishing_attempts,
        spam_attempts=spam_attempts,
        classes=classes,
        years=years,
        majors=majors,
        emails=emails,
        facilities=facilities,
        selected_class=selected_class,
        selected_year=selected_year,
        selected_major=selected_major,
        selected_email=selected_email,
        selected_facility=selected_facility,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page_num,
        total_pages=total_pages,
        prev_url=prev_url,
        next_url=next_url,
    )


@bp.route('/inspector/reset-user', methods=['POST'])
@login_required
def reset_inspector_user():
    if not current_user.is_admin:
        abort(403)
    username = request.form.get('username', '').strip()
    if not username:
        return jsonify({'error': 'Username is required.'}), 400
    user = get_user(username)
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    reset_user_inspector_state(username)
    return jsonify({'success': True, 'message': f'Inspector reset for {username}.'})


@bp.route('/inspector/reset-bulk', methods=['POST'])
@login_required
def reset_inspector_bulk():
    if not current_user.is_admin:
        abort(403)
    scope = request.form.get('scope', '').strip()
    if scope not in {'filtered', 'all'}:
        return jsonify({'error': 'Invalid scope.'}), 400

    class_filter = request.form.get('class_name', '').strip()
    year_filter = request.form.get('academic_year', '').strip()
    major_filter = request.form.get('major', '').strip()
    facility_filter = request.form.get('facility', '').strip()

    users = list_all_users()
    filtered_users = []
    for user in users:
        if user.is_admin:
            continue
        if scope == 'filtered':
            if class_filter and user.class_name != class_filter:
                continue
            if year_filter and user.academic_year != year_filter:
                continue
            if major_filter and user.major != major_filter:
                continue
            if facility_filter and user.facility != facility_filter:
                continue
        filtered_users.append(user.username)

    count = reset_users_inspector_state(filtered_users)
    label = 'filtered users' if scope == 'filtered' else 'all users'
    return jsonify(
        {
            'success': True,
            'count': count,
            'message': f'Inspector reset for {count} {label}.',
        }
    )


@bp.route('/reports/generate', methods=['POST'])
@login_required
def generate_report():
    """Generate a CSV report, upload to S3, return a pre-signed download URL."""
    if not current_user.is_admin:
        abort(403)

    report_type = request.form.get('report_type', 'summary')
    class_filter = request.form.get('class_name', '').strip()
    year_filter = request.form.get('academic_year', '').strip()
    major_filter = request.form.get('major', '').strip()
    facility_filter = request.form.get('facility', '').strip()

    attempts = list_all_attempts()
    if class_filter:
        attempts = [a for a in attempts if a.get('class_name') == class_filter]
    if year_filter:
        attempts = [a for a in attempts if a.get('academic_year') == year_filter]
    if major_filter:
        attempts = [a for a in attempts if a.get('major') == major_filter]
    if facility_filter:
        attempts = [a for a in attempts if a.get('facility') == facility_filter]

    # Enrich with quiz titles
    for a in attempts:
        quiz = get_quiz(a['quiz_id'])
        a['quiz_title'] = quiz['title'] if quiz else 'Unknown'

    # Build CSV in memory
    output = io.StringIO()
    if report_type == 'detailed':
        # Detailed: per-cohort per-quiz
        writer = csv.writer(output)
        writer.writerow(['Class', 'Academic Year', 'Major', 'Facility', 'Quiz', 'Attempts', 'Average Score (%)'])
        grouped = {}
        for a in attempts:
            key = (
                a.get('class_name', 'unknown'),
                a.get('academic_year', 'unknown'),
                a.get('major', 'unknown'),
                a.get('facility', 'unknown'),
                a.get('quiz_title', 'Unknown'),
            )
            if key not in grouped:
                grouped[key] = {'count': 0, 'total_pct': 0.0}
            grouped[key]['count'] += 1
            grouped[key]['total_pct'] += float(a.get('percentage', 0))
        for (class_name, academic_year, major, facility, quiz_title), stats in grouped.items():
            count = stats['count']
            avg = round(stats['total_pct'] / count, 1) if count > 0 else 0
            writer.writerow([class_name, academic_year, major, facility, quiz_title, count, avg])
    else:
        # Summary: cohort averages
        writer = csv.writer(output)
        writer.writerow(['Class', 'Academic Year', 'Major', 'Facility', 'Attempts', 'Average Score (%)'])
        grouped = {}
        for a in attempts:
            key = (
                a.get('class_name', 'unknown'),
                a.get('academic_year', 'unknown'),
                a.get('major', 'unknown'),
                a.get('facility', 'unknown'),
            )
            if key not in grouped:
                grouped[key] = {'count': 0, 'total_pct': 0.0}
            grouped[key]['count'] += 1
            grouped[key]['total_pct'] += float(a.get('percentage', 0))
        for (class_name, academic_year, major, facility), stats in grouped.items():
            count = stats['count']
            avg = round(stats['total_pct'] / count, 1) if count > 0 else 0
            writer.writerow([class_name, academic_year, major, facility, count, avg])

    # Upload to S3
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
    s3_key = f'reports/{now}_{report_type}_report.csv'
    bucket = current_app.config['S3_BUCKET']

    current_app.s3_client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=output.getvalue().encode('utf-8'),
        ContentType='text/csv',
    )

    # Generate pre-signed URL (1 hour)
    download_url = current_app.s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': s3_key},
        ExpiresIn=3600,
    )

    return jsonify({'download_url': download_url, 'filename': s3_key.split('/')[-1]})


@bp.route('/reports/inspector/generate', methods=['POST'])
@login_required
def generate_inspector_report():
    """Generate an inspector CSV report, upload to S3, return a pre-signed URL."""
    if not current_user.is_admin:
        abort(403)

    try:
        class_filter = request.form.get('class_name', '').strip()
        year_filter = request.form.get('academic_year', '').strip()
        major_filter = request.form.get('major', '').strip()
        facility_filter = request.form.get('facility', '').strip()
        email_filter = request.form.get('email', '')
        date_from = request.form.get('date_from', '').strip()
        date_to = request.form.get('date_to', '').strip()
        report_scope = request.form.get('report_scope', 'email')

        attempts = list_inspector_attempts_anonymous()
        if class_filter:
            attempts = [a for a in attempts if a.get('class_name') == class_filter]
        if year_filter:
            attempts = [a for a in attempts if a.get('academic_year') == year_filter]
        if major_filter:
            attempts = [a for a in attempts if a.get('major') == major_filter]
        if facility_filter:
            attempts = [a for a in attempts if a.get('facility') == facility_filter]
        if email_filter:
            attempts = [a for a in attempts if a.get('email_file') == email_filter]
        if date_from or date_to:
            def parse_date(value, end_of_day=False):
                if not value:
                    return None
                if end_of_day:
                    return datetime.fromisoformat(f'{value}T23:59:59+00:00')
                return datetime.fromisoformat(f'{value}T00:00:00+00:00')

            start_dt = parse_date(date_from, end_of_day=False)
            end_dt = parse_date(date_to, end_of_day=True)

            def in_range(item):
                submitted_at = item.get('submitted_at')
                if not submitted_at:
                    return False
                try:
                    submitted_dt = datetime.fromisoformat(submitted_at)
                except ValueError:
                    return False
                if start_dt and submitted_dt < start_dt:
                    return False
                if end_dt and submitted_dt > end_dt:
                    return False
                return True

            attempts = [a for a in attempts if in_range(a)]

        output = io.StringIO()
        writer = csv.writer(output)
        header = [
            'Class',
            'Academic Year',
            'Major',
            'Facility',
        ]
        if report_scope != 'cohort':
            header.append('Email')
        header += [
            'Attempts',
            'Correct Count',
            'Correct %',
            'Phishing Count',
            'Spam Count',
        ]
        writer.writerow(header)
        grouped = {}
        for a in attempts:
            key_parts = [
                a.get('class_name', 'unknown'),
                a.get('academic_year', 'unknown'),
                a.get('major', 'unknown'),
                a.get('facility', 'unknown'),
            ]
            if report_scope != 'cohort':
                key_parts.append(a.get('email_file', 'unknown'))
            key = tuple(key_parts)
            if key not in grouped:
                grouped[key] = {'count': 0, 'correct': 0, 'phishing': 0, 'spam': 0}
            grouped[key]['count'] += 1
            if a.get('is_correct'):
                grouped[key]['correct'] += 1
            if a.get('classification') == 'Phishing':
                grouped[key]['phishing'] += 1
            if a.get('classification') == 'Spam':
                grouped[key]['spam'] += 1
        for key, stats in grouped.items():
            if report_scope == 'cohort':
                class_name, academic_year, major, facility = key
                email_file = None
            else:
                class_name, academic_year, major, facility, email_file = key
            count = stats['count']
            correct_pct = round((stats['correct'] / count * 100), 1) if count > 0 else 0
            row = [class_name, academic_year, major, facility]
            if report_scope != 'cohort':
                row.append(email_file)
            row += [
                count,
                stats['correct'],
                correct_pct,
                stats['phishing'],
                stats['spam'],
            ]
            writer.writerow(row)

        now = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
        scope_suffix = 'cohort' if report_scope == 'cohort' else 'by_email'
        s3_key = f'reports/{now}_inspector_{scope_suffix}_report.csv'
        bucket = current_app.config['S3_BUCKET']

        current_app.s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=output.getvalue().encode('utf-8'),
            ContentType='text/csv',
        )

        download_url = current_app.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': s3_key},
            ExpiresIn=3600,
        )

        return jsonify({'download_url': download_url, 'filename': s3_key.split('/')[-1]})
    except Exception:
        current_app.logger.exception('Failed to generate inspector report')
        return jsonify({'error': 'Failed to generate inspector report.'}), 500
