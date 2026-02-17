import csv
import io
from datetime import datetime, timezone

import boto3
from flask import abort, current_app, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.dashboard import bp
from app.models import (
    count_users,
    get_distinct_groups,
    get_quiz,
    get_responses_by_question,
    list_all_attempts,
    list_all_users,
    list_attempts_by_group,
    list_attempts_by_quiz,
    list_quizzes,
)


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

    # Group stats
    groups = get_distinct_groups()
    group_stats = []
    for group in groups:
        group_attempts = list_attempts_by_group(group)
        count = len(group_attempts)
        if count > 0:
            avg = round(sum(float(a.get('percentage', 0)) for a in group_attempts) / count, 1)
        else:
            avg = 0
        group_stats.append({'group': group, 'count': count, 'avg': avg})

    # Recent activity (last 10)
    recent = sorted(attempts, key=lambda a: a.get('completed_at', ''), reverse=True)[:10]
    # Enrich with quiz title
    for r in recent:
        quiz = get_quiz(r['quiz_id'])
        r['quiz_title'] = quiz['title'] if quiz else 'Unknown'

    # Selected group filter
    selected_group = request.args.get('group', '')

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
        groups=groups,
        recent=recent,
        selected_group=selected_group,
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

    # Per-group stats
    groups = get_distinct_groups()
    per_group = {}
    for group in groups:
        group_attempts = list_attempts_by_group(group)
        count = len(group_attempts)
        if count > 0:
            avg = round(sum(float(a.get('percentage', 0)) for a in group_attempts) / count, 1)
        else:
            avg = 0
        per_group[group] = {'count': count, 'avg': avg}

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
    groups = get_distinct_groups()
    return render_template('admin/reports.html', groups=groups)


@bp.route('/reports/generate', methods=['POST'])
@login_required
def generate_report():
    """Generate a CSV report, upload to S3, return a pre-signed download URL."""
    if not current_user.is_admin:
        abort(403)

    report_type = request.form.get('report_type', 'summary')
    group_filter = request.form.get('group', '')

    # Gather data
    if group_filter:
        attempts = list_attempts_by_group(group_filter)
    else:
        attempts = list_all_attempts()

    # Enrich with quiz titles
    for a in attempts:
        quiz = get_quiz(a['quiz_id'])
        a['quiz_title'] = quiz['title'] if quiz else 'Unknown'

    # Build CSV in memory
    output = io.StringIO()
    if report_type == 'detailed':
        writer = csv.writer(output)
        writer.writerow(['Username', 'Group', 'Quiz', 'Score', 'Total', 'Percentage', 'Completed At'])
        for a in attempts:
            writer.writerow([
                a['username'],
                a.get('group', ''),
                a.get('quiz_title', ''),
                a['score'],
                a['total'],
                float(a.get('percentage', 0)),
                a.get('completed_at', ''),
            ])
    else:
        # Summary: group averages
        groups = get_distinct_groups()
        writer = csv.writer(output)
        writer.writerow(['Group', 'Attempts', 'Average Score (%)'])
        for group in groups:
            group_attempts = list_attempts_by_group(group)
            count = len(group_attempts)
            avg = round(sum(float(a.get('percentage', 0)) for a in group_attempts) / count, 1) if count > 0 else 0
            writer.writerow([group, count, avg])

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
