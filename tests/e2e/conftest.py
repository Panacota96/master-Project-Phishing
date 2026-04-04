"""Playwright E2E fixtures: spin up a live Flask server and seed sample data."""

import importlib
import os
import threading
import time
from typing import Callable

import pytest
import boto3
from moto import mock_aws
from werkzeug.serving import make_server

root_conftest = importlib.import_module("tests.conftest")
_create_dynamodb_tables = root_conftest._create_dynamodb_tables
_create_s3_bucket = root_conftest._create_s3_bucket
_create_sqs_queues = root_conftest._create_sqs_queues
create_app = importlib.import_module("app").create_app


def _create_e2e_tables(region: str = 'eu-west-3'):
    dynamodb = boto3.resource('dynamodb', region_name=region)

    users = os.environ.get('DYNAMODB_USERS', 'e2e-users')
    quizzes = os.environ.get('DYNAMODB_QUIZZES', 'e2e-quizzes')
    attempts = os.environ.get('DYNAMODB_ATTEMPTS', 'e2e-attempts')
    responses = os.environ.get('DYNAMODB_RESPONSES', 'e2e-responses')
    inspector = os.environ.get('DYNAMODB_INSPECTOR', 'e2e-inspector')
    inspector_anon = os.environ.get('DYNAMODB_INSPECTOR_ANON', 'e2e-inspector-anon')
    answer_key_overrides = os.environ.get('DYNAMODB_ANSWER_KEY_OVERRIDES', 'e2e-answer-key-overrides')
    cohort_tokens = os.environ.get('DYNAMODB_COHORT_TOKENS', 'e2e-cohort-tokens')
    threat_cache = os.environ.get('DYNAMODB_THREAT_CACHE', 'e2e-threat-cache')
    campaigns = os.environ.get('DYNAMODB_CAMPAIGNS', 'e2e-campaigns')
    campaign_events = os.environ.get('DYNAMODB_CAMPAIGN_EVENTS', 'e2e-campaign-events')
    bugs = os.environ.get('DYNAMODB_BUGS', 'e2e-bugs')

    dynamodb.create_table(
        TableName=users,
        KeySchema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
        AttributeDefinitions=[
            {'AttributeName': 'username', 'AttributeType': 'S'},
            {'AttributeName': 'email', 'AttributeType': 'S'},
            {'AttributeName': 'group', 'AttributeType': 'S'},
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'email-index',
                'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
            },
            {
                'IndexName': 'group-index',
                'KeySchema': [
                    {'AttributeName': 'group', 'KeyType': 'HASH'},
                    {'AttributeName': 'username', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
        BillingMode='PAY_PER_REQUEST',
    )

    dynamodb.create_table(
        TableName=quizzes,
        KeySchema=[{'AttributeName': 'quiz_id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'quiz_id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
    )

    dynamodb.create_table(
        TableName=attempts,
        KeySchema=[
            {'AttributeName': 'username', 'KeyType': 'HASH'},
            {'AttributeName': 'quiz_id', 'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'username', 'AttributeType': 'S'},
            {'AttributeName': 'quiz_id', 'AttributeType': 'S'},
            {'AttributeName': 'completed_at', 'AttributeType': 'S'},
            {'AttributeName': 'group', 'AttributeType': 'S'},
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'quiz-index',
                'KeySchema': [
                    {'AttributeName': 'quiz_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'completed_at', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
            {
                'IndexName': 'group-index',
                'KeySchema': [
                    {'AttributeName': 'group', 'KeyType': 'HASH'},
                    {'AttributeName': 'completed_at', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
        BillingMode='PAY_PER_REQUEST',
    )

    dynamodb.create_table(
        TableName=responses,
        KeySchema=[
            {'AttributeName': 'username_quiz_id', 'KeyType': 'HASH'},
            {'AttributeName': 'question_id', 'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'username_quiz_id', 'AttributeType': 'S'},
            {'AttributeName': 'question_id', 'AttributeType': 'S'},
            {'AttributeName': 'quiz_question_id', 'AttributeType': 'S'},
            {'AttributeName': 'username', 'AttributeType': 'S'},
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'quiz-question-index',
                'KeySchema': [
                    {'AttributeName': 'quiz_question_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'username', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
        BillingMode='PAY_PER_REQUEST',
    )

    dynamodb.create_table(
        TableName=inspector,
        KeySchema=[
            {'AttributeName': 'username', 'KeyType': 'HASH'},
            {'AttributeName': 'submitted_at', 'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'username', 'AttributeType': 'S'},
            {'AttributeName': 'submitted_at', 'AttributeType': 'S'},
            {'AttributeName': 'group', 'AttributeType': 'S'},
            {'AttributeName': 'email_file', 'AttributeType': 'S'},
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'group-index',
                'KeySchema': [
                    {'AttributeName': 'group', 'KeyType': 'HASH'},
                    {'AttributeName': 'submitted_at', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
            {
                'IndexName': 'email-index',
                'KeySchema': [
                    {'AttributeName': 'email_file', 'KeyType': 'HASH'},
                    {'AttributeName': 'submitted_at', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
        BillingMode='PAY_PER_REQUEST',
    )

    dynamodb.create_table(
        TableName=inspector_anon,
        KeySchema=[
            {'AttributeName': 'attempt_id', 'KeyType': 'HASH'},
            {'AttributeName': 'submitted_at', 'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'attempt_id', 'AttributeType': 'S'},
            {'AttributeName': 'submitted_at', 'AttributeType': 'S'},
        ],
        BillingMode='PAY_PER_REQUEST',
    )

    dynamodb.create_table(
        TableName=answer_key_overrides,
        KeySchema=[{'AttributeName': 'email_file', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'email_file', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
    )

    dynamodb.create_table(
        TableName=bugs,
        KeySchema=[{'AttributeName': 'bug_id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'bug_id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
    )

    dynamodb.create_table(
        TableName=cohort_tokens,
        KeySchema=[{'AttributeName': 'token', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'token', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
    )

    dynamodb.create_table(
        TableName=threat_cache,
        KeySchema=[{'AttributeName': 'cache_key', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'cache_key', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
    )

    dynamodb.create_table(
        TableName=campaigns,
        KeySchema=[{'AttributeName': 'campaign_id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[
            {'AttributeName': 'campaign_id', 'AttributeType': 'S'},
            {'AttributeName': 'cohort', 'AttributeType': 'S'},
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'cohort-index',
                'KeySchema': [{'AttributeName': 'cohort', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
        BillingMode='PAY_PER_REQUEST',
    )

    dynamodb.create_table(
        TableName=campaign_events,
        KeySchema=[
            {'AttributeName': 'campaign_id', 'KeyType': 'HASH'},
            {'AttributeName': 'event_id', 'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'campaign_id', 'AttributeType': 'S'},
            {'AttributeName': 'event_id', 'AttributeType': 'S'},
            {'AttributeName': 'event_type', 'AttributeType': 'S'},
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'event-type-index',
                'KeySchema': [
                    {'AttributeName': 'event_type', 'KeyType': 'HASH'},
                    {'AttributeName': 'event_id', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
        BillingMode='PAY_PER_REQUEST',
    )


@pytest.fixture(autouse=True)
def enable_sso(monkeypatch):
    """Force SSO button visible in E2E flows."""
    monkeypatch.setenv('MSAL_CLIENT_ID', 'test-client-id')
    monkeypatch.setenv('MSAL_CLIENT_SECRET', 'test-client-secret')


@pytest.fixture()
def e2e_app(monkeypatch):
    """Create a shared Flask app with mocked AWS services for E2E tests."""
    with mock_aws():
        monkeypatch.setenv('DYNAMODB_USERS', 'e2e-users')
        monkeypatch.setenv('DYNAMODB_QUIZZES', 'e2e-quizzes')
        monkeypatch.setenv('DYNAMODB_ATTEMPTS', 'e2e-attempts')
        monkeypatch.setenv('DYNAMODB_RESPONSES', 'e2e-responses')
        monkeypatch.setenv('DYNAMODB_INSPECTOR', 'e2e-inspector')
        monkeypatch.setenv('DYNAMODB_INSPECTOR_ANON', 'e2e-inspector-anon')
        monkeypatch.setenv('DYNAMODB_ANSWER_KEY_OVERRIDES', 'e2e-answer-key-overrides')
        monkeypatch.setenv('DYNAMODB_COHORT_TOKENS', 'e2e-cohort-tokens')
        monkeypatch.setenv('DYNAMODB_THREAT_CACHE', 'e2e-threat-cache')
        monkeypatch.setenv('DYNAMODB_CAMPAIGNS', 'e2e-campaigns')
        monkeypatch.setenv('DYNAMODB_CAMPAIGN_EVENTS', 'e2e-campaign-events')
        monkeypatch.setenv('DYNAMODB_BUGS', 'e2e-bugs')
        monkeypatch.setenv('S3_BUCKET', 'e2e-bucket')
        monkeypatch.setenv('MSAL_CLIENT_ID', 'e2e-client-id')
        monkeypatch.setenv('MSAL_CLIENT_SECRET', 'e2e-client-secret')

        _create_e2e_tables()

        s3 = boto3.client('s3', region_name='eu-west-3')
        s3.create_bucket(
            Bucket='e2e-bucket',
            CreateBucketConfiguration={'LocationConstraint': 'eu-west-3'},
        )

        sqs = boto3.client('sqs', region_name='eu-west-3')
        reg = sqs.create_queue(QueueName='e2e-registration-queue')
        camp = sqs.create_queue(QueueName='e2e-campaign-queue')
        monkeypatch.setenv('SQS_REGISTRATION_QUEUE_URL', reg['QueueUrl'])
        monkeypatch.setenv('SQS_CAMPAIGN_QUEUE_URL', camp['QueueUrl'])

        application = create_app()
        application.config['TESTING'] = True
        application.config['WTF_CSRF_ENABLED'] = False
        yield application


@pytest.fixture()
def e2e_live_server(e2e_app):
    """Run the Flask app with mocked AWS on an ephemeral port."""
    server = make_server('127.0.0.1', 0, e2e_app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{server.server_address[0]}:{server.server_port}"

    # Give the server a brief moment to start accepting connections.
    time.sleep(0.1)
    try:
        yield base_url
    finally:
        server.shutdown()
        thread.join(timeout=2)


@pytest.fixture()
def e2e_base_url(e2e_live_server) -> str:
    return e2e_live_server


@pytest.fixture()
def e2e_seed_admin(e2e_app):
    with e2e_app.app_context():
        from app.models import create_user
        return create_user(
            'admin',
            'admin@test.com',
            'admin123',
            is_admin=True,
            group='admin',
            class_name='Class A',
            academic_year='2025',
            major='Security',
        )


@pytest.fixture()
def e2e_seed_user(e2e_app):
    with e2e_app.app_context():
        from app.models import create_user
        return create_user(
            'testuser',
            'test@test.com',
            'password123',
            group='engineering',
            class_name='Class A',
            academic_year='2025',
            major='CS',
        )


@pytest.fixture()
def e2e_seed_quiz(e2e_app):
    with e2e_app.app_context():
        from app.models import create_quiz
        return create_quiz(
            quiz_id='quiz-test',
            title='Test Quiz',
            description='A test quiz',
            video_url='/static/videos/placeholder.mp4',
            questions=[
                {
                    'question_id': 'q1',
                    'question_text': 'What is phishing?',
                    'explanation': 'Phishing is a social engineering attack.',
                    'answers': [
                        {'answer_id': 'q1a1', 'answer_text': 'A type of fishing', 'is_correct': False},
                        {'answer_id': 'q1a2', 'answer_text': 'A social engineering attack', 'is_correct': True},
                    ],
                },
                {
                    'question_id': 'q2',
                    'question_text': 'What is spear phishing?',
                    'explanation': 'Targeted phishing against specific individuals.',
                    'answers': [
                        {'answer_id': 'q2a1', 'answer_text': 'Targeted phishing', 'is_correct': True},
                        {'answer_id': 'q2a2', 'answer_text': 'Mass email spam', 'is_correct': False},
                    ],
                },
            ],
        )


@pytest.fixture()
def login_user(page, e2e_base_url, e2e_seed_user) -> Callable[[str, str], None]:
    """Log in as a standard user via the UI."""

    def _login(username: str = 'testuser', password: str = 'password123'):
        page.goto(f"{e2e_base_url}/auth/login")
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")
        page.wait_for_url(f"{e2e_base_url}/quiz/", timeout=5000)

    return _login


@pytest.fixture()
def login_admin(page, e2e_base_url, e2e_seed_admin) -> Callable[[str, str], None]:
    """Log in as an administrator via the UI."""

    def _login(username: str = 'admin', password: str = 'admin123'):
        page.goto(f"{e2e_base_url}/auth/login")
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")
        page.wait_for_url(f"{e2e_base_url}/quiz/", timeout=5000)

    return _login


@pytest.fixture()
def seed_inspector_samples(e2e_app):
    """Upload a minimal set of inspector emails to the mocked S3 bucket."""
    filenames = [
        'fakeinvoice-urgency-spoofing-socialeng.eml',
    ]
    with e2e_app.app_context():
        for name in filenames:
            body = f"Subject: {name}\n\nThis is a test body for {name}".encode('utf-8')
            e2e_app.s3_client.put_object(
                Bucket=e2e_app.config['S3_BUCKET'],
                Key=f"eml-samples/{name}",
                Body=body,
            )
    return filenames


# Re-export login helper so existing imports continue to work even when this
# conftest is imported first by pytest.
def login(client, username, password):
    return client.post(
        '/auth/login',
        data={'username': username, 'password': password},
        follow_redirects=True,
    )
