from flask import flash, redirect, render_template, session, url_for
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

    # One-attempt lock: check if user already completed this quiz
    existing = get_attempt(current_user.username, quiz_id)
    if existing:
        flash('You have already completed this quiz.', 'warning')
        return render_template(
            'quiz/results.html',
            score=int(existing['score']),
            total=int(existing['total']),
            quiz_id=quiz_id,
            already_completed=True,
        )

    questions = quiz.get('questions', [])
    if not questions:
        flash('This quiz has no questions yet.', 'warning')
        return redirect(url_for('quiz.quiz_list'))

    session['quiz_score'] = 0
    session['quiz_total'] = 0
    session['quiz_id'] = quiz_id
    session['question_ids'] = [q['question_id'] for q in questions]
    session['current_index'] = 0
    return redirect(url_for('quiz.take_question'))


@bp.route('/question', methods=['GET', 'POST'])
@login_required
def take_question():
    question_ids = session.get('question_ids', [])
    current_index = session.get('current_index', 0)
    quiz_id = session.get('quiz_id')

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
    )


@bp.route('/finish')
@login_required
def finish_quiz():
    quiz_id = session.get('quiz_id')
    score = session.get('quiz_score', 0)
    total = session.get('quiz_total', 0)

    if quiz_id and total > 0:
        # Conditional write — fails silently if attempt already exists
        create_attempt(
            username=current_user.username,
            quiz_id=quiz_id,
            score=score,
            total=total,
            group=current_user.group,
        )
        mark_quiz_completed(current_user.username)

    # Clean up session
    for key in ('quiz_score', 'quiz_total', 'quiz_id', 'question_ids', 'current_index'):
        session.pop(key, None)

    return render_template('quiz/results.html', score=score, total=total, quiz_id=quiz_id)


@bp.route('/history')
@login_required
def history():
    attempts = list_attempts_by_user(current_user.username)
    # Enrich with quiz titles
    for attempt in attempts:
        quiz = get_quiz(attempt['quiz_id'])
        attempt['quiz_title'] = quiz['title'] if quiz else 'Unknown Quiz'
    attempts.sort(key=lambda a: a.get('completed_at', ''), reverse=True)
    return render_template('quiz/history.html', attempts=attempts)
