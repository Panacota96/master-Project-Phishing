import csv
import io
import time
import requests
from datetime import datetime, timezone

from flask import abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.dashboard import bp
from app.inspector.answer_key import ANSWER_KEY
from app.models import (
    count_users,
    create_bug_report,
    delete_user,
    get_distinct_cohorts,
    get_quiz,
    get_user,
    list_all_users,
    list_all_attempts,
    list_attempts_by_quiz,
    list_bug_reports,
    list_inspector_attempts_anonymous,
    list_quizzes,
    reset_user_inspector_state,
    reset_users_inspector_state,
)

# Simple in-memory cache for threat feed
THREAT_CACHE = {
    'data': [],
    'timestamp': 0
}

@bp.route('/api/threat-feed')
@login_required
def api_threat_feed():
    """Fetch and defang real-time phishing URLs from OpenPhish."""
    if not current_user.is_admin:
        abort(403)
        
    # Check cache (1 hour expiry)
    now = time.time()
    if now - THREAT_CACHE['timestamp'] < 3600 and THREAT_CACHE['data']:
        return jsonify(THREAT_CACHE['data'])
        
    try:
        # OpenPhish free feed provides raw URLs
        resp = requests.get('https://openphish.com/feed.txt', timeout=5)
        if resp.status_code == 200:
            urls = resp.text.splitlines()[:10] # Top 10 recent
            defanged = []
            for u in urls:
                if not u.strip(): continue
                # Defang for safety
                safe_url = u.replace('http', 'hxxp').replace('.', '[.]')
                # Simple heuristic to guess target (very rough)
                target = "Unknown"
                if 'paypal' in u: target = "PayPal"
                elif 'microsoft' in u or 'office365' in u: target = "Microsoft"
                elif 'google' in u or 'gmail' in u: target = "Google"
                elif 'amazon' in u: target = "Amazon"
                elif 'apple' in u or 'icloud' in u: target = "Apple"
                
                defanged.append({'target': target, 'url': safe_url})
            
            THREAT_CACHE['data'] = defanged
            THREAT_CACHE['timestamp'] = now
            return jsonify(defanged)
            
    except Exception as e:
        current_app.logger.error(f"Threat feed fetch failed: {e}")
        
    return jsonify([]) # Return empty list on failure


@bp.route('/users')
@login_required
def list_users():
    if not current_user.is_admin:
        abort(403)
    users = list_all_users()
    return render_template('admin/users.html', users=users)


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
    
    cohort_risk = {} # {(class, year, major): {signal_misses: 0, quiz_fails: 0, total_actions: 0}}
    
    for a in inspector_attempts:
        key = (a.get('class_name', 'unknown'), a.get('academic_year', 'unknown'), a.get('major', 'unknown'))
        if key not in cohort_risk:
            cohort_risk[key] = {'signal_misses': 0, 'quiz_fails': 0, 'total_actions': 0}
        
        cohort_risk[key]['total_actions'] += 1
        if not a.get('is_correct'):
            cohort_risk[key]['signal_misses'] += 1
            
    for a in quiz_attempts:
        key = (a.get('class_name', 'unknown'), a.get('academic_year', 'unknown'), a.get('major', 'unknown'))
        if key not in cohort_risk:
            cohort_risk[key] = {'signal_misses': 0, 'quiz_fails': 0, 'total_actions': 0}
        
        cohort_risk[key]['total_actions'] += 1
        if float(a.get('percentage', 0)) < 70:
            cohort_risk[key]['quiz_fails'] += 1
            
    risk_data = []
    for (c, y, m), stats in cohort_risk.items():
        if stats['total_actions'] > 0:
            # Risk = Average of (miss rate + fail rate)
            miss_rate = (stats['signal_misses'] / stats['total_actions']) * 100
            fail_rate = (stats['quiz_fails'] / stats['total_actions']) * 100
            risk_score = round((miss_rate + fail_rate) / 2, 1)

            risk_data.append({
                'class_name': c,
                'academic_year': y,
                'major': m,
                'risk_score': risk_score,
                'label': f"{c} | {y} | {m}",
                'level': 'High' if risk_score > 60 else 'Medium' if risk_score > 30 else 'Low'
            })

    risk_data.sort(key=lambda x: x['risk_score'], reverse=True)

    return render_template('admin/risk_dashboard.html', risk_data=risk_data)


@bp.route('/inspector/answer-key')
@login_required
def inspector_answer_key():
    if not current_user.is_admin:
        abort(403)

    # Format answer key for template
    sorted_keys = sorted(ANSWER_KEY.keys())
    items = []
    for filename in sorted_keys:
        items.append({
            'filename': filename,
            'classification': ANSWER_KEY[filename]['classification'],
            'signals': ANSWER_KEY[filename]['signals']
        })

    return render_template('admin/inspector_answer_key.html', items=items)


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

    # Cohort stats (class/year/major)
    cohort_stats = {}
    for attempt in attempts:
        class_name = attempt.get('class_name', 'unknown')
        academic_year = attempt.get('academic_year', 'unknown')
        major = attempt.get('major', 'unknown')
        key = (class_name, academic_year, major)
        if key not in cohort_stats:
            cohort_stats[key] = {'count': 0, 'total_pct': 0.0}
        cohort_stats[key]['count'] += 1
        cohort_stats[key]['total_pct'] += float(attempt.get('percentage', 0))

    group_stats = []
    for (class_name, academic_year, major), stats in cohort_stats.items():
        count = stats['count']
        avg = round(stats['total_pct'] / count, 1) if count > 0 else 0
        group_stats.append({
            'class_name': class_name,
            'academic_year': academic_year,
            'major': major,
            'count': count,
            'avg': avg,
            'label': f'{class_name} | {academic_year} | {major}',
        })

    # Inspector analytics
    inspector_attempts = list_inspector_attempts_anonymous()
    inspector_total = len(inspector_attempts)
    inspector_correct = sum(1 for a in inspector_attempts if a.get('is_correct'))
    inspector_phishing = sum(1 for a in inspector_attempts if a.get('classification') == 'Phishing')
    inspector_spam = sum(1 for a in inspector_attempts if a.get('classification') == 'Spam')

    # Signal Accuracy Stats
    signal_stats = {}  # {signal_alias: {expected: 0, identified: 0}}
    for attempt in inspector_attempts:
        expected = attempt.get('expected_signals', [])
        selected = attempt.get('selected_signals', [])
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
        inspector_recent=[],
        inspector_per_email=inspector_per_email,
        signal_accuracy=signal_accuracy,
    )


@bp.route('/api/stats')
@login_required
def api_stats():
    """Live statistics endpoint — polled by the dashboard every 30 seconds."""
    if not current_user.is_admin:
        abort(403)

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

    # Per-cohort stats (class/year/major)
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

    return jsonify({
        'total_users': total_users,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'avg_score': avg_score,
        'per_group': per_group,
    })


@bp.route('/reports')
@login_required
def reports():
    if not current_user.is_admin:
        abort(403)
    cohorts = get_distinct_cohorts()
    classes = sorted({c[0] for c in cohorts})
    years = sorted({c[1] for c in cohorts})
    majors = sorted({c[2] for c in cohorts})
    return render_template(
        'admin/reports.html',
        classes=classes,
        years=years,
        majors=majors,
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

    selected_class = request.args.get('class_name', '')
    selected_year = request.args.get('academic_year', '')
    selected_major = request.args.get('major', '')
    selected_email = request.args.get('email', '')
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
    for (class_name, academic_year, major), stats in aggregated.items():
        attempts_count = stats['attempts']
        correct_pct = round((stats['correct'] / attempts_count * 100), 1) if attempts_count > 0 else 0
        aggregated_rows.append({
            'class_name': class_name,
            'academic_year': academic_year,
            'major': major,
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
        selected_class=selected_class,
        selected_year=selected_year,
        selected_major=selected_major,
        selected_email=selected_email,
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

    attempts = list_all_attempts()
    if class_filter:
        attempts = [a for a in attempts if a.get('class_name') == class_filter]
    if year_filter:
        attempts = [a for a in attempts if a.get('academic_year') == year_filter]
    if major_filter:
        attempts = [a for a in attempts if a.get('major') == major_filter]

    # Enrich with quiz titles
    for a in attempts:
        quiz = get_quiz(a['quiz_id'])
        a['quiz_title'] = quiz['title'] if quiz else 'Unknown'

    # Build CSV in memory
    output = io.StringIO()
    if report_type == 'detailed':
        # Detailed: per-cohort per-quiz
        writer = csv.writer(output)
        writer.writerow(['Class', 'Academic Year', 'Major', 'Quiz', 'Attempts', 'Average Score (%)'])
        grouped = {}
        for a in attempts:
            key = (
                a.get('class_name', 'unknown'),
                a.get('academic_year', 'unknown'),
                a.get('major', 'unknown'),
                a.get('quiz_title', 'Unknown'),
            )
            if key not in grouped:
                grouped[key] = {'count': 0, 'total_pct': 0.0}
            grouped[key]['count'] += 1
            grouped[key]['total_pct'] += float(a.get('percentage', 0))
        for (class_name, academic_year, major, quiz_title), stats in grouped.items():
            count = stats['count']
            avg = round(stats['total_pct'] / count, 1) if count > 0 else 0
            writer.writerow([class_name, academic_year, major, quiz_title, count, avg])
    else:
        # Summary: cohort averages
        writer = csv.writer(output)
        writer.writerow(['Class', 'Academic Year', 'Major', 'Attempts', 'Average Score (%)'])
        grouped = {}
        for a in attempts:
            key = (
                a.get('class_name', 'unknown'),
                a.get('academic_year', 'unknown'),
                a.get('major', 'unknown'),
            )
            if key not in grouped:
                grouped[key] = {'count': 0, 'total_pct': 0.0}
            grouped[key]['count'] += 1
            grouped[key]['total_pct'] += float(a.get('percentage', 0))
        for (class_name, academic_year, major), stats in grouped.items():
            count = stats['count']
            avg = round(stats['total_pct'] / count, 1) if count > 0 else 0
            writer.writerow([class_name, academic_year, major, count, avg])

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
                class_name, academic_year, major = key
                email_file = None
            else:
                class_name, academic_year, major, email_file = key
            count = stats['count']
            correct_pct = round((stats['correct'] / count * 100), 1) if count > 0 else 0
            row = [class_name, academic_year, major]
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
