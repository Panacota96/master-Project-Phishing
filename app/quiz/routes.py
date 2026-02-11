from flask import render_template, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app import db
from app.quiz import bp
from app.quiz.forms import QuestionForm
from app.models import Quiz, Question, Answer, QuizAttempt


@bp.route('/')
@login_required
def quiz_list():
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()
    return render_template('quiz/quiz_list.html', quizzes=quizzes)


@bp.route('/<int:quiz_id>/start')
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    session['quiz_score'] = 0
    session['quiz_total'] = 0
    session['quiz_id'] = quiz_id
    questions = quiz.questions.all()
    if not questions:
        flash('This quiz has no questions yet.', 'warning')
        return redirect(url_for('quiz.quiz_list'))
    session['question_ids'] = [q.id for q in questions]
    session['current_index'] = 0
    return redirect(url_for('quiz.take_question'))


@bp.route('/question', methods=['GET', 'POST'])
@login_required
def take_question():
    question_ids = session.get('question_ids', [])
    current_index = session.get('current_index', 0)

    if current_index >= len(question_ids):
        return redirect(url_for('quiz.finish_quiz'))

    question = Question.query.get_or_404(question_ids[current_index])
    answers = question.answers.all()
    form = QuestionForm()
    form.answer.choices = [(a.id, a.answer_text) for a in answers]

    show_explanation = False
    selected_answer = None
    is_correct = False

    if form.validate_on_submit():
        selected_answer = Answer.query.get(form.answer.data)
        if selected_answer and selected_answer.is_correct:
            session['quiz_score'] = session.get('quiz_score', 0) + 1
            is_correct = True
        session['quiz_total'] = session.get('quiz_total', 0) + 1
        session['current_index'] = current_index + 1
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
        attempt = QuizAttempt(
            user_id=current_user.id,
            quiz_id=quiz_id,
            score=score,
            total=total,
        )
        db.session.add(attempt)
        db.session.commit()

    # Clean up session
    for key in ('quiz_score', 'quiz_total', 'quiz_id', 'question_ids', 'current_index'):
        session.pop(key, None)

    return render_template('quiz/results.html', score=score, total=total, quiz_id=quiz_id)


@bp.route('/history')
@login_required
def history():
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id)\
        .order_by(QuizAttempt.completed_at.desc()).all()
    return render_template('quiz/history.html', attempts=attempts)
