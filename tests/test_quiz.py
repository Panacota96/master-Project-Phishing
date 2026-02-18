"""Tests for quiz routes — quiz lock, per-question responses."""

from conftest import login


class TestQuizList:
    def test_quiz_list_requires_login(self, client):
        resp = client.get('/quiz/')
        assert resp.status_code == 302  # Redirect to login

    def test_quiz_list_shows_quizzes(self, client, seed_user, seed_quiz):
        login(client, 'testuser', 'password123')
        resp = client.get('/quiz/')
        assert resp.status_code == 200
        assert b'Test Quiz' in resp.data

    def test_quiz_list_shows_completed_badge(self, client, app, seed_user, seed_quiz):
        # First, create an attempt for this user
        with app.app_context():
            from app.models import create_attempt
            create_attempt('testuser', 'quiz-test', 2, 2, 'engineering')

        login(client, 'testuser', 'password123')
        resp = client.get('/quiz/')
        assert b'Completed' in resp.data
        assert b'Already Completed' in resp.data


class TestQuizLock:
    def test_start_quiz_redirects_if_already_completed(self, client, app, seed_user, seed_quiz):
        with app.app_context():
            from app.models import create_attempt
            create_attempt('testuser', 'quiz-test', 2, 2, 'engineering')

        login(client, 'testuser', 'password123')
        resp = client.get('/quiz/quiz-test/start', follow_redirects=True)
        assert b'You have already completed this quiz' in resp.data

    def test_start_quiz_works_for_new_attempt(self, client, seed_user, seed_quiz):
        login(client, 'testuser', 'password123')
        resp = client.get('/quiz/quiz-test/start')
        assert resp.status_code == 302  # Redirect to take_question
        assert '/quiz/question' in resp.headers.get('Location', '')


class TestTakeQuiz:
    def test_take_question_renders(self, client, seed_user, seed_quiz):
        login(client, 'testuser', 'password123')
        client.get('/quiz/quiz-test/start')
        resp = client.get('/quiz/question')
        assert resp.status_code == 200
        assert b'What is phishing?' in resp.data

    def test_submit_answer_saves_response(self, client, app, seed_user, seed_quiz):
        login(client, 'testuser', 'password123')
        client.get('/quiz/quiz-test/start')

        # Submit correct answer for q1
        resp = client.post('/quiz/question', data={'answer': 'q1a2'}, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Correct' in resp.data

        # Verify response was saved
        with app.app_context():
            from app.models import get_responses
            responses = get_responses('testuser', 'quiz-test')
            assert len(responses) == 1
            assert responses[0]['is_correct'] is True


class TestQuizHistory:
    def test_history_shows_attempts(self, client, app, seed_user, seed_quiz):
        with app.app_context():
            from app.models import create_attempt
            create_attempt('testuser', 'quiz-test', 1, 2, 'engineering')

        login(client, 'testuser', 'password123')
        resp = client.get('/quiz/history')
        assert resp.status_code == 200
        assert b'Test Quiz' in resp.data

    def test_history_empty(self, client, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.get('/quiz/history')
        assert b"haven't taken any quizzes" in resp.data.lower() or b'Start one now' in resp.data
