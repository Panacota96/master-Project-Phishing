"""Tests for the registration worker Lambda handler."""

import json
import os
import sys
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _make_sqs_event(body: dict) -> dict:
    return {
        'Records': [
            {
                'messageId': 'test-msg-1',
                'body': json.dumps(body),
            }
        ]
    }


@pytest.fixture(autouse=True)
def worker_env(monkeypatch):
    monkeypatch.setenv('DYNAMODB_USERS', 'worker-test-users')
    monkeypatch.setenv('AWS_REGION_NAME', 'eu-west-3')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'eu-west-3')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('SES_FROM_EMAIL', 'no-reply@test.example.com')
    monkeypatch.setenv('APP_LOGIN_URL', 'http://localhost/auth/login')
    monkeypatch.setenv('SNS_REGISTRATION_ARN', '')


@pytest.fixture()
def aws_resources():
    """Set up mocked DynamoDB users table and SES."""
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-3')
        dynamodb.create_table(
            TableName='worker-test-users',
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

        # Verify SES sender identity so send_email doesn't 400
        ses = boto3.client('ses', region_name='eu-west-3')
        ses.verify_email_identity(EmailAddress='no-reply@test.example.com')

        yield dynamodb


def _get_handler():
    """Import worker handler fresh (re-imports to pick up monkeypatched env vars)."""
    import importlib
    import registration_worker.handler as m
    importlib.reload(m)
    return m


def test_worker_creates_user(aws_resources):
    from werkzeug.security import generate_password_hash

    m = _get_handler()
    event = _make_sqs_event({
        'username': 'student1',
        'email': 'student1@test.com',
        'password_hash': generate_password_hash('SecurePass1!'),
        'class_name': 'Class A',
        'academic_year': '2025',
        'major': 'CS',
        'facility': 'Paris',
        'group': 'default',
    })

    m.handler(event, {})

    table = aws_resources.Table('worker-test-users')
    item = table.get_item(Key={'username': 'student1'}).get('Item')
    assert item is not None
    assert item['email'] == 'student1@test.com'
    assert item['class_name'] == 'Class A'
    assert item['role'] == 'student'


def test_worker_skips_duplicate(aws_resources):
    """If the user already exists, the worker does not raise and does not overwrite."""
    from werkzeug.security import generate_password_hash

    m = _get_handler()
    payload = {
        'username': 'dup_user',
        'email': 'dup@test.com',
        'password_hash': generate_password_hash('SecurePass1!'),
        'class_name': 'Class A',
        'academic_year': '2025',
        'major': 'CS',
        'facility': 'Paris',
        'group': 'default',
    }
    event = _make_sqs_event(payload)

    m.handler(event, {})
    # Call again — should not raise
    m.handler(event, {})

    table = aws_resources.Table('worker-test-users')
    items = table.scan()['Items']
    assert len([i for i in items if i['username'] == 'dup_user']) == 1


def test_worker_sends_email(aws_resources, monkeypatch):
    """Verify SES send_email is called with the correct recipient."""
    from werkzeug.security import generate_password_hash

    sent = []

    import registration_worker.handler as m
    import importlib
    importlib.reload(m)

    original_send = m._ses.send_email

    def fake_send(**kwargs):
        sent.append(kwargs)
        return {'MessageId': 'test-123'}

    monkeypatch.setattr(m, '_ses', type('FakeSES', (), {'send_email': staticmethod(fake_send)})())

    event = _make_sqs_event({
        'username': 'emailtest',
        'email': 'emailtest@test.com',
        'password_hash': generate_password_hash('SecurePass1!'),
        'class_name': 'Class A',
        'academic_year': '2025',
        'major': 'CS',
        'facility': 'Paris',
        'group': 'default',
    })

    m.handler(event, {})

    assert len(sent) == 1
    assert sent[0]['Destination']['ToAddresses'] == ['emailtest@test.com']
    assert sent[0]['Source'] == 'no-reply@test.example.com'
