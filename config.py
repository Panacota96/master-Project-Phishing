import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_APP_SECRETS_CACHE: dict[str, Any] | None = None
_APP_SECRETS_CACHE_ARN: str | None = None


def _get_app_secrets() -> dict[str, Any]:
    """Fetch and cache the shared app secret bundle from Secrets Manager."""
    global _APP_SECRETS_CACHE, _APP_SECRETS_CACHE_ARN

    secret_arn = os.environ.get("SECRET_ARN", "").strip()
    if not secret_arn:
        return {}

    if (
        _APP_SECRETS_CACHE is not None
        and _APP_SECRETS_CACHE_ARN == secret_arn
    ):
        return _APP_SECRETS_CACHE

    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    try:
        region = os.environ.get("AWS_REGION_NAME", "eu-west-3")
        client = boto3.client("secretsmanager", region_name=region)
        resp = client.get_secret_value(SecretId=secret_arn)
        data = json.loads(resp["SecretString"])
        if not isinstance(data, dict):
            raise ValueError("secret payload must be a JSON object")
    except (
        ClientError,
        BotoCoreError,
        json.JSONDecodeError,
        KeyError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            f"Failed to load application secrets from {secret_arn}: {exc}"
        ) from exc

    _APP_SECRETS_CACHE = data
    _APP_SECRETS_CACHE_ARN = secret_arn
    return data


def _resolve_secret_key() -> str:
    """Return the Flask SECRET_KEY.

    When running on AWS Lambda the ``SECRET_ARN`` environment variable points
    to a Secrets Manager secret that holds the key as a JSON object
    ``{"SECRET_KEY": "..."}`` alongside other credentials.  We fetch the value
    at startup so the plaintext key is never stored as a Lambda environment
    variable (where it is visible in the AWS console).

    Falls back to the ``SECRET_KEY`` environment variable (or the insecure
    development default) when ``SECRET_ARN`` is absent — this preserves
    backward-compatibility for local development and unit tests.
    """
    secret_arn = os.environ.get("SECRET_ARN", "").strip()
    if secret_arn:
        secret_key = _get_app_secrets().get("SECRET_KEY")
        if secret_key:
            return secret_key

        env_secret_key = os.environ.get("SECRET_KEY", "")
        if env_secret_key:
            logger.warning(
                "SECRET_ARN is set but SECRET_KEY was not found in Secrets Manager; "
                "falling back to SECRET_KEY env var"
            )
            return env_secret_key

        raise RuntimeError(
            "SECRET_ARN is set but SECRET_KEY could not be resolved from Secrets "
            "Manager and no SECRET_KEY env fallback is configured"
        )
    return os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")


def _resolve_msal_client_secret() -> str:
    """Return the MSAL client secret from Secrets Manager or env var."""
    secret_arn = os.environ.get("SECRET_ARN", "").strip()
    if secret_arn:
        msal_client_secret = _get_app_secrets().get("MSAL_CLIENT_SECRET")
        if msal_client_secret:
            return msal_client_secret

        logger.warning(
            "SECRET_ARN is set but MSAL_CLIENT_SECRET was not found in Secrets "
            "Manager; falling back to MSAL_CLIENT_SECRET env var"
        )
    return os.environ.get("MSAL_CLIENT_SECRET", "")


class Config:
    SECRET_KEY = _resolve_secret_key()

    # Flask-WTF CSRF — allow requests through CloudFront where the Referer
    # header is the CloudFront domain, not the API Gateway origin.
    # The CSRF token itself is still validated; only the referrer/origin header
    # check is relaxed.
    WTF_CSRF_SSL_STRICT = False

    # AWS / DynamoDB
    AWS_REGION = os.environ.get('AWS_REGION_NAME', 'eu-west-3')
    DYNAMODB_USERS = os.environ.get('DYNAMODB_USERS', 'en-garde-prod-users')
    DYNAMODB_QUIZZES = os.environ.get('DYNAMODB_QUIZZES', 'en-garde-prod-quizzes')
    DYNAMODB_ATTEMPTS = os.environ.get('DYNAMODB_ATTEMPTS', 'en-garde-prod-attempts')
    DYNAMODB_RESPONSES = os.environ.get('DYNAMODB_RESPONSES', 'en-garde-prod-responses')
    DYNAMODB_INSPECTOR = os.environ.get('DYNAMODB_INSPECTOR', 'en-garde-prod-inspector-attempts')
    DYNAMODB_INSPECTOR_ANON = os.environ.get(
        'DYNAMODB_INSPECTOR_ANON',
        'en-garde-prod-inspector-attempts-anon',
    )
    DYNAMODB_BUGS = os.environ.get('DYNAMODB_BUGS', 'en-garde-prod-bugs')
    DYNAMODB_ANSWER_KEY_OVERRIDES = os.environ.get(
        'DYNAMODB_ANSWER_KEY_OVERRIDES',
        'en-garde-prod-answer-key-overrides',
    )
    DYNAMODB_THREAT_CACHE = os.environ.get('DYNAMODB_THREAT_CACHE', 'en-garde-prod-threat-cache')
    DYNAMODB_CAMPAIGNS = os.environ.get('DYNAMODB_CAMPAIGNS', 'en-garde-prod-campaigns')
    DYNAMODB_CAMPAIGN_EVENTS = os.environ.get('DYNAMODB_CAMPAIGN_EVENTS', 'en-garde-prod-campaign-events')

    # S3
    S3_BUCKET = os.environ.get('S3_BUCKET', 'en-garde-prod-eu-west-3')

    DYNAMODB_COHORT_TOKENS = os.environ.get('DYNAMODB_COHORT_TOKENS', 'en-garde-prod-cohort-tokens')

    # SQS / SES (QR self-registration)
    SQS_REGISTRATION_QUEUE_URL = os.environ.get('SQS_REGISTRATION_QUEUE_URL', '')
    SQS_CAMPAIGN_QUEUE_URL = os.environ.get('SQS_CAMPAIGN_QUEUE_URL', '')
    SES_FROM_EMAIL = os.environ.get('SES_FROM_EMAIL', '')
    APP_LOGIN_URL = os.environ.get('APP_LOGIN_URL', 'http://localhost:5000/auth/login')

    # DynamoDB Local (for local development)
    DYNAMODB_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', None)
    S3_ENDPOINT = os.environ.get('S3_ENDPOINT', None)

    # Redis / ElastiCache
    REDIS_ENDPOINT = os.environ.get('REDIS_ENDPOINT', '')
    REDIS_URL = os.environ.get('REDIS_URL', '')
    REDIS_USE_TLS = os.environ.get('REDIS_USE_TLS', 'false').lower() == 'true'

    # ── Microsoft 365 / Azure AD SSO (optional) ─────────────────────────────
    # Set all three variables to enable the "Sign in with Microsoft" button.
    # Leave them empty (default) to disable SSO entirely.
    MSAL_CLIENT_ID = os.environ.get('MSAL_CLIENT_ID', '')
    MSAL_CLIENT_SECRET = _resolve_msal_client_secret()
    # e.g. "https://login.microsoftonline.com/<tenant-id>/v2.0" or
    #       "https://login.microsoftonline.com/common/v2.0" for multi-tenant.
    MSAL_AUTHORITY = os.environ.get(
        'MSAL_AUTHORITY',
        'https://login.microsoftonline.com/common/v2.0',
    )
    # Scopes requested during the OAuth2 authorisation request.
    MSAL_SCOPES = ['openid', 'profile', 'email', 'User.Read', 'GroupMember.Read.All']
    # Optional: Azure AD group object-IDs that map to local roles.
    # Leave empty to treat all SSO users as ordinary students.
    MSAL_ADMIN_GROUP_ID = os.environ.get('MSAL_ADMIN_GROUP_ID', '')
    MSAL_INSTRUCTOR_GROUP_ID = os.environ.get('MSAL_INSTRUCTOR_GROUP_ID', '')

    # Threat feed cache (optional DynamoDB TTL table)
    THREAT_CACHE_TTL_SECONDS = int(os.environ.get('THREAT_CACHE_TTL_SECONDS', '3600'))

    # Inspector pool tuning (per-cohort overrides stored in memory or DynamoDB)
    DYNAMODB_INSPECTOR_CONFIG = os.environ.get('DYNAMODB_INSPECTOR_CONFIG', '')
    INSPECTOR_POOL_SIZE_DEFAULT = int(os.environ.get('INSPECTOR_POOL_SIZE_DEFAULT', '8'))
    INSPECTOR_MAX_SPAM_DEFAULT = int(os.environ.get('INSPECTOR_MAX_SPAM_DEFAULT', '3'))
    INSPECTOR_SPAM_RATIO_DEFAULT = float(os.environ.get('INSPECTOR_SPAM_RATIO_DEFAULT', '0.35'))

    # Quiz experience toggles
    QUIZ_MAX_RETRIES_DEFAULT = int(os.environ.get('QUIZ_MAX_RETRIES_DEFAULT', '1'))
    QUIZ_TIMER_DEFAULT = int(os.environ.get('QUIZ_TIMER_DEFAULT', '0'))
    QUIZ_ADAPTIVE_DEFAULT = os.environ.get('QUIZ_ADAPTIVE_DEFAULT', 'false').lower() == 'true'

    # Campaign + notifications (optional)
    CAMPAIGN_LAMBDA_ARN = os.environ.get('CAMPAIGN_LAMBDA_ARN', '')
    VALIDATION_EMAIL_TEMPLATE = os.environ.get('VALIDATION_EMAIL_TEMPLATE', '')
