import time

from flask import current_app, flash, jsonify, redirect, render_template, session, url_for
from flask_login import current_user, login_required

from app.models import (
    create_attempt,
    get_attempt,
    get_quiz,
    list_attempts_by_user,
    list_quizzes,
    mark_quiz_completed,
    save_response,
)
from app.quiz import bp
from app.quiz.forms import QuestionForm


@bp.route('/')
@login_required
def quiz_list():
    quizzes = list_quizzes()
    # Attach completion status for the current user
    for quiz in quizzes:
        attempt = get_attempt(current_user.username, quiz['quiz_id'])
        quiz['user_completed'] = attempt is not None
    return render_template('quiz/quiz_list.html', quizzes=quizzes)


@bp.route('/<quiz_id>/start')
@login_required
def start_quiz(quiz_id):
    quiz = get_quiz(quiz_id)
    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('quiz.quiz_list'))

    max_retries = int(quiz.get('max_retries', current_app.config.get('QUIZ_MAX_RETRIES_DEFAULT', 1)))
    adaptive = bool(quiz.get('adaptive', current_app.config.get('QUIZ_ADAPTIVE_DEFAULT', False)))
    time_limit_seconds = int(quiz.get('time_limit_seconds', current_app.config.get('QUIZ_TIMER_DEFAULT', 0)))

    # One-attempt lock: check if user already completed this quiz
    existing = get_attempt(current_user.username, quiz_id)
    if existing and max_retries <= int(existing.get('attempt_number', 1)):
        flash('You have already completed this quiz.', 'warning')
        video_url = quiz.get('video_url')
        return render_template(
            'quiz/results.html',
            score=int(existing['score']),
            total=int(existing['total']),
            quiz_id=quiz_id,
            already_completed=True,
            video_url=video_url,
        )
    elif existing:
        session['quiz_attempt_number'] = int(existing.get('attempt_number', 1)) + 1
    else:
        session['quiz_attempt_number'] = 1

    video_url = quiz.get('video_url')
    if video_url:
        watched = session.get('quiz_video_watched', {}).get(quiz_id)
        if not watched:
            return redirect(url_for('quiz.video_gate', quiz_id=quiz_id))

    questions = quiz.get('questions', [])
    if not questions:
        flash('This quiz has no questions yet.', 'warning')
        return redirect(url_for('quiz.quiz_list'))

    session['quiz_score'] = 0
    session['quiz_total'] = 0
    session['quiz_id'] = quiz_id
    ordered_questions = (
        sorted(
            questions,
            key=lambda q: q.get('difficulty', 1),
            reverse=session.get('quiz_attempt_number', 1) > 1,
        )
        if adaptive
        else questions
    )
    session['question_ids'] = [q['question_id'] for q in ordered_questions]
    session['current_index'] = 0
    if time_limit_seconds:
        session['quiz_time_limit'] = time_limit_seconds
        session['quiz_started_at'] = time.time()
    return redirect(url_for('quiz.take_question'))


@bp.route('/<quiz_id>/video')
@login_required
def video_gate(quiz_id):
    quiz = get_quiz(quiz_id)
    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('quiz.quiz_list'))
    video_url = quiz.get('video_url')
    if not video_url:
        return redirect(url_for('quiz.start_quiz', quiz_id=quiz_id))
    return render_template('quiz/video_gate.html', quiz=quiz, video_url=video_url)


@bp.route('/<quiz_id>/video-watched', methods=['POST'])
@login_required
def video_watched(quiz_id):
    quiz = get_quiz(quiz_id)
    if not quiz:
        return jsonify({'error': 'Quiz not found.'}), 404
    video_url = quiz.get('video_url')
    if not video_url:
        return jsonify({'error': 'Video not configured.'}), 400
    watched = session.get('quiz_video_watched', {})
    watched[quiz_id] = True
    session['quiz_video_watched'] = watched
    return jsonify({'success': True})


@bp.route('/question', methods=['GET', 'POST'])
@login_required
def take_question():
    question_ids = session.get('question_ids', [])
    current_index = session.get('current_index', 0)
    quiz_id = session.get('quiz_id')

    time_limit = session.get('quiz_time_limit')
    started_at = session.get('quiz_started_at')
    elapsed = None
    if time_limit and started_at:
        elapsed = time.time() - started_at
        if elapsed > time_limit:
            flash('Time is up for this quiz.', 'warning')
            return redirect(url_for('quiz.finish_quiz'))

    if current_index >= len(question_ids):
        return redirect(url_for('quiz.finish_quiz'))

    quiz = get_quiz(quiz_id)
    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('quiz.quiz_list'))

    # Find the current question from the embedded quiz data
    questions = quiz.get('questions', [])
    question_id = question_ids[current_index]
    question = None
    for q in questions:
        if q['question_id'] == question_id:
            question = q
            break

    if not question:
        flash('Question not found.', 'danger')
        return redirect(url_for('quiz.quiz_list'))

    answers = question.get('answers', [])
    form = QuestionForm()
    form.answer.choices = [(a['answer_id'], a['answer_text']) for a in answers]

    show_explanation = False
    selected_answer = None
    is_correct = False

    if form.validate_on_submit():
        selected_id = form.answer.data
        # Find the selected answer
        for a in answers:
            if a['answer_id'] == selected_id:
                selected_answer = a
                break

        if selected_answer and selected_answer.get('is_correct'):
            session['quiz_score'] = session.get('quiz_score', 0) + 1
            is_correct = True

        session['quiz_total'] = session.get('quiz_total', 0) + 1
        session['current_index'] = current_index + 1

        # Save per-question response to DynamoDB
        save_response(
            username=current_user.username,
            quiz_id=quiz_id,
            question_id=question_id,
            selected_answer_id=selected_id,
            is_correct=is_correct,
        )

        show_explanation = True

    progress = int((current_index / len(question_ids)) * 100)
    remaining_seconds = max(int(time_limit - elapsed), 0) if time_limit and elapsed is not None else None

    return render_template(
        'quiz/take_quiz.html',
        question=question,
        form=form,
        show_explanation=show_explanation,
        selected_answer=selected_answer,
        is_correct=is_correct,
        current=current_index + 1,
        total=len(question_ids),
        progress=progress,
        time_limit=time_limit,
        remaining_seconds=remaining_seconds,
    )


@bp.route('/finish')
@login_required
def finish_quiz():
    quiz_id = session.get('quiz_id')
    score = session.get('quiz_score', 0)
    total = session.get('quiz_total', 0)
    attempt_number = session.get('quiz_attempt_number', 1)
    time_limit_seconds = session.get('quiz_time_limit')
    quiz = get_quiz(quiz_id) if quiz_id else None
    video_url = quiz.get('video_url') if quiz else None

    if quiz_id and total > 0:
        # Conditional write — fails silently if attempt already exists
        create_attempt(
            username=current_user.username,
            quiz_id=quiz_id,
            score=score,
            total=total,
            group=current_user.group,
            class_name=current_user.class_name,
            academic_year=current_user.academic_year,
            major=current_user.major,
            allow_overwrite=attempt_number > 1,
            attempt_number=attempt_number,
            time_limit_seconds=time_limit_seconds,
        )
        mark_quiz_completed(current_user.username)

    # Clean up session
    cleanup_keys = (
        'quiz_score',
        'quiz_total',
        'quiz_id',
        'question_ids',
        'current_index',
        'quiz_attempt_number',
        'quiz_time_limit',
        'quiz_started_at',
    )
    for key in cleanup_keys:
        session.pop(key, None)

    return render_template(
        'quiz/results.html',
        score=score,
        total=total,
        quiz_id=quiz_id,
        video_url=video_url,
    )


@bp.route('/history')
@login_required
def history():
    attempts = list_attempts_by_user(current_user.username)
    quizzes = list_quizzes()
    total_quizzes = len(quizzes)
    completed_count = len(attempts)

    avg_score = 0
    if completed_count > 0:
        avg_score = sum(float(a.get('percentage', 0)) for a in attempts) / completed_count

    # Enrich with quiz titles
    for attempt in attempts:
        quiz = get_quiz(attempt['quiz_id'])
        attempt['quiz_title'] = quiz['title'] if quiz else 'Unknown Quiz'

    attempts.sort(key=lambda a: a.get('completed_at', ''), reverse=True)

    # Calculate rank
    rank = "Novice"
    badge_color = "secondary"
    if completed_count >= total_quizzes / 2:
        if avg_score >= 90:
            rank = "Cyber Sentinel"
            badge_color = "success"
        elif avg_score >= 70:
            rank = "Defender"
            badge_color = "primary"
        else:
            rank = "Trainee"
            badge_color = "info"

    return render_template(
        'quiz/history.html',
        attempts=attempts,
        total_quizzes=total_quizzes,
        completed_count=completed_count,
        avg_score=round(avg_score, 1),
        rank=rank,
        badge_color=badge_color,
        completion_pct=int((completed_count / total_quizzes * 100) if total_quizzes > 0 else 0)
    )
