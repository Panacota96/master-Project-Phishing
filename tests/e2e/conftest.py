"""
Pytest fixtures for Playwright E2E tests.

These fixtures start a real Flask dev server and provide authenticated
browser sessions for admin and student users.  The server uses an
in-process moto mock so no real AWS credentials are required.

Skip the entire module when ``playwright`` is not installed so that the
normal ``make test`` run (which only installs ``requirements.txt``) is
not broken.
"""

from __future__ import annotations

import os
import threading
import time

import boto3
import pytest

playwright = pytest.importorskip("playwright", reason="playwright not installed; skipping E2E tests")

from moto import mock_aws  # noqa: E402
from playwright.sync_api import Page, sync_playwright  # noqa: E402  (after importorskip)

# ── app import is deferred so env vars are in place first ──────────────────


def _set_env():
    """Set environment variables required by the Flask app."""
    os.environ.update(
        {
            "AWS_ACCESS_KEY_ID": "testing",
            "AWS_SECRET_ACCESS_KEY": "testing",
            "AWS_DEFAULT_REGION": "eu-west-3",
            "AWS_REGION_NAME": "eu-west-3",
            "SECRET_KEY": "e2e-test-secret",
            "DYNAMODB_USERS": "e2e-users",
            "DYNAMODB_QUIZZES": "e2e-quizzes",
            "DYNAMODB_ATTEMPTS": "e2e-attempts",
            "DYNAMODB_RESPONSES": "e2e-responses",
            "DYNAMODB_INSPECTOR": "e2e-inspector",
            "DYNAMODB_INSPECTOR_ANON": "e2e-inspector-anon",
            "DYNAMODB_ANSWER_KEY_OVERRIDES": "e2e-answer-key-overrides",
            "DYNAMODB_COHORT_TOKENS": "e2e-cohort-tokens",
            "DYNAMODB_THREAT_CACHE": "e2e-threat-cache",
            "DYNAMODB_CAMPAIGNS": "e2e-campaigns",
            "DYNAMODB_CAMPAIGN_EVENTS": "e2e-campaign-events",
            "DYNAMODB_BUGS": "e2e-bugs",
            "S3_BUCKET": "e2e-bucket",
            "SQS_REGISTRATION_QUEUE_URL": "",
            "SQS_CAMPAIGN_QUEUE_URL": "",
            "SES_FROM_EMAIL": "no-reply@test.example.com",
        }
    )


def _create_tables(dynamodb):
    """Create the DynamoDB tables the app expects."""
    dynamodb.create_table(
        TableName="e2e-users",
        KeySchema=[{"AttributeName": "username", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "username", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"},
            {"AttributeName": "group", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "email-index",
                "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "group-index",
                "KeySchema": [
                    {"AttributeName": "group", "KeyType": "HASH"},
                    {"AttributeName": "username", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    dynamodb.create_table(
        TableName="e2e-quizzes",
        KeySchema=[{"AttributeName": "quiz_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "quiz_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    dynamodb.create_table(
        TableName="e2e-attempts",
        KeySchema=[
            {"AttributeName": "username", "KeyType": "HASH"},
            {"AttributeName": "quiz_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "username", "AttributeType": "S"},
            {"AttributeName": "quiz_id", "AttributeType": "S"},
            {"AttributeName": "group", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "quiz_id-index",
                "KeySchema": [{"AttributeName": "quiz_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "group-index",
                "KeySchema": [
                    {"AttributeName": "group", "KeyType": "HASH"},
                    {"AttributeName": "quiz_id", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    dynamodb.create_table(
        TableName="e2e-responses",
        KeySchema=[
            {"AttributeName": "username_quiz_id", "KeyType": "HASH"},
            {"AttributeName": "question_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "username_quiz_id", "AttributeType": "S"},
            {"AttributeName": "question_id", "AttributeType": "S"},
            {"AttributeName": "quiz_question_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "quiz_question_id-index",
                "KeySchema": [
                    {"AttributeName": "quiz_question_id", "KeyType": "HASH"}
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    for table_name in [
        "e2e-inspector",
        "e2e-inspector-anon",
        "e2e-answer-key-overrides",
        "e2e-cohort-tokens",
        "e2e-threat-cache",
        "e2e-campaigns",
        "e2e-campaign-events",
        "e2e-bugs",
    ]:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )


@pytest.fixture(scope="session")
def live_server(tmp_path_factory):
    """
    Start a live Flask server backed by moto mocks for the whole test session.

    Yields the base URL (e.g. ``http://localhost:5100``).
    """
    _set_env()
    mock = mock_aws()
    mock.start()

    region = "eu-west-3"
    dynamodb = boto3.resource("dynamodb", region_name=region)
    s3 = boto3.client("s3", region_name=region)
    _create_tables(dynamodb)
    s3.create_bucket(
        Bucket="e2e-bucket",
        CreateBucketConfiguration={"LocationConstraint": region},
    )

    # Import app after moto is up so create_app uses mocked AWS
    from app import create_app

    flask_app = create_app()
    flask_app.config["TESTING"] = False
    flask_app.config["WTF_CSRF_ENABLED"] = False

    # Seed an admin and a student user
    from werkzeug.security import generate_password_hash

    users_table = dynamodb.Table("e2e-users")
    users_table.put_item(
        Item={
            "username": "e2e_admin",
            "email": "admin@e2e.test",
            "password_hash": generate_password_hash("Admin@e2e1"),
            "is_admin": True,
            "group": "e2e-group",
            "class_name": "E2E",
            "academic_year": "2024",
            "major": "CS",
        }
    )
    users_table.put_item(
        Item={
            "username": "e2e_student",
            "email": "student@e2e.test",
            "password_hash": generate_password_hash("Student@e2e1"),
            "is_admin": False,
            "group": "e2e-group",
            "class_name": "E2E",
            "academic_year": "2024",
            "major": "CS",
        }
    )

    port = 5199
    server_thread = threading.Thread(
        target=lambda: flask_app.run(host="127.0.0.1", port=port, use_reloader=False),
        daemon=True,
    )
    server_thread.start()
    # Wait until the server is ready
    base = f"http://127.0.0.1:{port}"
    for _ in range(20):
        try:
            import urllib.request

            urllib.request.urlopen(f"{base}/auth/login", timeout=1)
            break
        except Exception:
            time.sleep(0.3)

    yield base

    mock.stop()


@pytest.fixture(scope="session")
def base_url(live_server):
    return live_server


@pytest.fixture
def page(live_server):
    """Provide a fresh Playwright page for each test."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        pg = context.new_page()
        yield pg
        context.close()
        browser.close()


def _login(page: Page, base_url: str, username: str, password: str):
    page.goto(f"{base_url}/auth/login")
    page.fill("input[name='username']", username)
    page.fill("input[name='password']", password)
    page.click("button[type='submit']")


@pytest.fixture
def authenticated_user(page: Page, base_url: str):
    """Log in as the student user; yields the page already authenticated."""
    _login(page, base_url, "e2e_student", "Student@e2e1")
    return page


@pytest.fixture
def authenticated_admin(page: Page, base_url: str):
    """Log in as the admin user; yields the page already authenticated."""
    _login(page, base_url, "e2e_admin", "Admin@e2e1")
    return page
