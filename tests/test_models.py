"""Tests for the DynamoDB data access layer (app/models.py)."""

from moto import mock_aws

from tests.conftest import login


class TestUserModel:
    def test_create_and_get_user(self, app):
        with app.app_context():
            from app.models import create_user, get_user
            user = create_user('john', 'john@test.com', 'secret', group='engineering')
            assert user.username == 'john'
            assert user.email == 'john@test.com'
            assert user.group == 'engineering'
            assert user.is_admin is False

            fetched = get_user('john')
            assert fetched is not None
            assert fetched.username == 'john'
            assert fetched.check_password('secret')
            assert not fetched.check_password('wrong')

    def test_get_user_not_found(self, app):
        with app.app_context():
            from app.models import get_user
            assert get_user('nonexistent') is None

    def test_get_user_by_email(self, app):
        with app.app_context():
            from app.models import create_user, get_user_by_email
            create_user('alice', 'alice@test.com', 'pass')
            found = get_user_by_email('alice@test.com')
            assert found is not None
            assert found.username == 'alice'

            assert get_user_by_email('nobody@test.com') is None

    def test_batch_create_users(self, app):
        with app.app_context():
            from app.models import batch_create_users, get_user
            users = [
                {'username': 'u1', 'email': 'u1@test.com', 'password': 'p1', 'group': 'hr'},
                {'username': 'u2', 'email': 'u2@test.com', 'password': 'p2', 'group': 'hr'},
            ]
            created, skipped = batch_create_users(users)
            assert created == 2
            assert skipped == []
            assert get_user('u1') is not None
            assert get_user('u2') is not None

    def test_batch_create_users_skips_existing(self, app, seed_admin):
        with app.app_context():
            from app.models import batch_create_users
            users = [
                {'username': 'admin', 'email': 'other@test.com', 'password': 'p', 'group': 'x'},
                {'username': 'new', 'email': 'new@test.com', 'password': 'p', 'group': 'x'},
            ]
            created, skipped = batch_create_users(users)
            assert created == 1
            assert 'admin' in skipped

    def test_list_users_by_group(self, app):
        with app.app_context():
            from app.models import create_user, list_users_by_group
            create_user('a', 'a@t.com', 'p', group='dev')
            create_user('b', 'b@t.com', 'p', group='dev')
            create_user('c', 'c@t.com', 'p', group='ops')

            devs = list_users_by_group('dev')
            assert len(devs) == 2
            ops = list_users_by_group('ops')
            assert len(ops) == 1

    def test_count_users(self, app, seed_admin, seed_user):
        with app.app_context():
            from app.models import count_users
            assert count_users() == 2

    def test_get_distinct_groups(self, app):
        with app.app_context():
            from app.models import create_user, get_distinct_groups
            create_user('x', 'x@t.com', 'p', group='beta')
            create_user('y', 'y@t.com', 'p', group='alpha')
            groups = get_distinct_groups()
            assert groups == ['alpha', 'beta']


class TestQuizModel:
    def test_create_and_get_quiz(self, app, seed_quiz):
        with app.app_context():
            from app.models import get_quiz
            quiz = get_quiz('quiz-test')
            assert quiz is not None
            assert quiz['title'] == 'Test Quiz'
            assert len(quiz['questions']) == 2

    def test_list_quizzes(self, app, seed_quiz):
        with app.app_context():
            from app.models import list_quizzes
            quizzes = list_quizzes()
            assert len(quizzes) == 1
            assert quizzes[0]['quiz_id'] == 'quiz-test'


class TestAttemptModel:
    def test_create_and_get_attempt(self, app):
        with app.app_context():
            from app.models import create_attempt, get_attempt
            result = create_attempt('testuser', 'quiz-1', 8, 10, 'engineering')
            assert result is not None
            assert result['score'] == 8

            fetched = get_attempt('testuser', 'quiz-1')
            assert fetched is not None
            assert int(fetched['score']) == 8

    def test_one_attempt_per_user_per_quiz(self, app):
        with app.app_context():
            from app.models import create_attempt
            first = create_attempt('user1', 'quiz-1', 5, 10, 'group1')
            assert first is not None
            second = create_attempt('user1', 'quiz-1', 9, 10, 'group1')
            assert second is None  # Conditional write should fail

    def test_list_attempts_by_user(self, app):
        with app.app_context():
            from app.models import create_attempt, list_attempts_by_user
            create_attempt('u1', 'q1', 5, 10, 'g')
            create_attempt('u1', 'q2', 7, 10, 'g')
            attempts = list_attempts_by_user('u1')
            assert len(attempts) == 2

    def test_list_attempts_by_group(self, app):
        with app.app_context():
            from app.models import create_attempt, list_attempts_by_group
            create_attempt('u1', 'q1', 5, 10, 'eng')
            create_attempt('u2', 'q1', 7, 10, 'eng')
            create_attempt('u3', 'q1', 9, 10, 'hr')
            eng = list_attempts_by_group('eng')
            assert len(eng) == 2


class TestResponseModel:
    def test_save_and_get_responses(self, app):
        with app.app_context():
            from app.models import get_responses, save_response
            save_response('user1', 'quiz1', 'q1', 'q1a2', True)
            save_response('user1', 'quiz1', 'q2', 'q2a1', False)

            responses = get_responses('user1', 'quiz1')
            assert len(responses) == 2

    def test_get_responses_by_question(self, app):
        with app.app_context():
            from app.models import get_responses_by_question, save_response
            save_response('u1', 'quiz1', 'q1', 'a1', True)
            save_response('u2', 'quiz1', 'q1', 'a2', False)
            save_response('u3', 'quiz1', 'q2', 'a1', True)

            q1_responses = get_responses_by_question('quiz1', 'q1')
            assert len(q1_responses) == 2
