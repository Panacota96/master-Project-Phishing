"""Pytest fixtures — mock AWS services with moto before the Flask app starts."""

import os

import boto3
import pytest
from moto import mock_aws


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    """Set environment variables for the test Flask app."""
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'eu-west-3')
    monkeypatch.setenv('AWS_REGION_NAME', 'eu-west-3')
    monkeypatch.setenv('SECRET_KEY', 'test-secret')
    monkeypatch.setenv('DYNAMODB_USERS', 'test-users')
    monkeypatch.setenv('DYNAMODB_QUIZZES', 'test-quizzes')
    monkeypatch.setenv('DYNAMODB_ATTEMPTS', 'test-attempts')
    monkeypatch.setenv('DYNAMODB_RESPONSES', 'test-responses')
    monkeypatch.setenv('S3_BUCKET', 'test-bucket')


def _create_dynamodb_tables(region='eu-west-3'):
    """Create the 4 DynamoDB tables that the app expects."""
    dynamodb = boto3.resource('dynamodb', region_name=region)

    # Users table
    dynamodb.create_table(
        TableName='test-users',
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

    # Quizzes table
    dynamodb.create_table(
        TableName='test-quizzes',
        KeySchema=[{'AttributeName': 'quiz_id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[
            {'AttributeName': 'quiz_id', 'AttributeType': 'S'},
        ],
        BillingMode='PAY_PER_REQUEST',
    )

    # Attempts table
    dynamodb.create_table(
        TableName='test-attempts',
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

    # Responses table
    dynamodb.create_table(
        TableName='test-responses',
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


def _create_s3_bucket(region='eu-west-3'):
    s3 = boto3.client('s3', region_name=region)
    s3.create_bucket(
        Bucket='test-bucket',
        CreateBucketConfiguration={'LocationConstraint': region},
    )


@pytest.fixture()
def app():
    """Create a Flask test app with mocked AWS services."""
    with mock_aws():
        _create_dynamodb_tables()
        _create_s3_bucket()

        from app import create_app
        application = create_app()
        application.config['TESTING'] = True
        application.config['WTF_CSRF_ENABLED'] = False

        yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture()
def seed_admin(app):
    """Create an admin user in the mocked DynamoDB."""
    with app.app_context():
        from app.models import create_user
        return create_user('admin', 'admin@test.com', 'admin123', is_admin=True, group='admin')


@pytest.fixture()
def seed_user(app):
    """Create a regular user."""
    with app.app_context():
        from app.models import create_user
        return create_user('testuser', 'test@test.com', 'password123', group='engineering')


@pytest.fixture()
def seed_quiz(app):
    """Create a sample quiz."""
    with app.app_context():
        from app.models import create_quiz
        return create_quiz(
            quiz_id='quiz-test',
            title='Test Quiz',
            description='A test quiz',
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


def login(client, username, password):
    """Helper to log in a user via the test client."""
    return client.post('/auth/login', data={
        'username': username,
        'password': password,
    }, follow_redirects=True)
