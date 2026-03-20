import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

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

    # S3
    S3_BUCKET = os.environ.get('S3_BUCKET', 'en-garde-prod-eu-west-3')

    # DynamoDB Local (for local development)
    DYNAMODB_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', None)
    S3_ENDPOINT = os.environ.get('S3_ENDPOINT', None)
