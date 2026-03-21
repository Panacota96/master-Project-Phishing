"""Tests for the QR self-registration flow (generic / token-free POC)."""

import json

import boto3

from tests.conftest import login

_VALID_REG_DATA = {
    'username': 'newstudent',
    'email': 'newstudent@test.com',
    'class_name': 'Class A',
    'academic_year': '2025',
    'major': 'CS',
    'facility': 'Paris',
    'password': 'SecurePass1!',
    'confirm_password': 'SecurePass1!',
}


# ─── GET /auth/register ───────────────────────────────────────────────────────

def test_register_get(client):
    """GET /auth/register returns the registration form (no token required)."""
    resp = client.get('/auth/register')
    assert resp.status_code == 200
    assert b'Create Your Account' in resp.data


# ─── POST /auth/register ──────────────────────────────────────────────────────

def test_register_post_success(client, app, sqs_queue):
    """Valid POST enqueues a message and shows the pending page."""
    app.config['SQS_REGISTRATION_QUEUE_URL'] = sqs_queue

    resp = client.post('/auth/register', data=_VALID_REG_DATA, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Account being created' in resp.data

    sqs = boto3.client('sqs', region_name='eu-west-3')
    msgs = sqs.receive_message(QueueUrl=sqs_queue, MaxNumberOfMessages=1)
    assert 'Messages' in msgs
    body = json.loads(msgs['Messages'][0]['Body'])
    assert body['username'] == 'newstudent'
    assert body['email'] == 'newstudent@test.com'
    assert 'password_hash' in body
    assert body['class_name'] == 'Class A'


def test_register_duplicate_username(client, app, seed_user, sqs_queue):
    """A duplicate username shows a form error."""
    app.config['SQS_REGISTRATION_QUEUE_URL'] = sqs_queue

    data = dict(_VALID_REG_DATA, username='testuser')  # seed_user username
    resp = client.post('/auth/register', data=data)
    assert resp.status_code == 200
    assert b'Username already taken' in resp.data


def test_register_duplicate_email(client, app, seed_user, sqs_queue):
    """A duplicate email shows a form error."""
    app.config['SQS_REGISTRATION_QUEUE_URL'] = sqs_queue

    data = dict(_VALID_REG_DATA, email='test@test.com')  # seed_user email
    resp = client.post('/auth/register', data=data)
    assert resp.status_code == 200
    assert b'already exists' in resp.data


def test_register_weak_password(client):
    """A weak password returns a form validation error."""
    data = dict(_VALID_REG_DATA, password='weak', confirm_password='weak')
    resp = client.post('/auth/register', data=data)
    assert resp.status_code == 200
    assert b'least 8' in resp.data or b'uppercase' in resp.data or b'number' in resp.data


# ─── GET/POST /auth/admin/generate-qr ────────────────────────────────────────

def test_generate_qr_requires_admin(client, seed_user):
    """Non-admin users get 403."""
    login(client, 'testuser', 'password123')
    resp = client.get('/auth/admin/generate-qr')
    assert resp.status_code == 403


def test_generate_qr_get_as_admin(client, seed_admin):
    """Admin GET returns the form page."""
    login(client, 'admin', 'admin123')
    resp = client.get('/auth/admin/generate-qr')
    assert resp.status_code == 200
    assert b'Generate Registration QR Code' in resp.data


def test_generate_qr_returns_png(client, seed_admin):
    """Admin POST returns a page with an embedded base64 PNG QR code."""
    login(client, 'admin', 'admin123')
    resp = client.post('/auth/admin/generate-qr', data={})
    assert resp.status_code == 200
    assert b'data:image/png;base64,' in resp.data
    assert b'Download PNG' in resp.data
