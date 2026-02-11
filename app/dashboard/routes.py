from flask import render_template, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.dashboard import bp
from app.models import User, Quiz, QuizAttempt


@bp.route('/')
@login_required
def index():
    if not current_user.is_admin:
        abort(403)

    total_users = User.query.count()
    total_attempts = QuizAttempt.query.count()

    avg_score_result = db.session.query(
        func.avg(QuizAttempt.score * 100.0 / QuizAttempt.total)
    ).scalar()
    avg_score = round(avg_score_result, 1) if avg_score_result else 0

    # Score distribution for chart (buckets: 0-20, 20-40, 40-60, 60-80, 80-100)
    score_distribution = [0, 0, 0, 0, 0]
    attempts = QuizAttempt.query.all()
    for attempt in attempts:
        pct = (attempt.score / attempt.total) * 100 if attempt.total > 0 else 0
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
    quizzes = Quiz.query.all()
    for quiz in quizzes:
        quiz_attempts = QuizAttempt.query.filter_by(quiz_id=quiz.id).all()
        count = len(quiz_attempts)
        if count > 0:
            avg = round(sum(a.score / a.total * 100 for a in quiz_attempts) / count, 1)
        else:
            avg = 0
        quiz_stats.append({'title': quiz.title, 'count': count, 'avg': avg})

    # Recent activity
    recent = QuizAttempt.query.order_by(QuizAttempt.completed_at.desc()).limit(10).all()

    return render_template(
        'dashboard/dashboard.html',
        total_users=total_users,
        total_attempts=total_attempts,
        avg_score=avg_score,
        score_distribution=score_distribution,
        quiz_stats=quiz_stats,
        recent=recent,
    )
