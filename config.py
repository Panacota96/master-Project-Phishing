import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # AWS / DynamoDB
    AWS_REGION = os.environ.get('AWS_REGION_NAME', 'eu-west-3')
    DYNAMODB_USERS = os.environ.get('DYNAMODB_USERS', 'phishing-app-prod-users')
    DYNAMODB_QUIZZES = os.environ.get('DYNAMODB_QUIZZES', 'phishing-app-prod-quizzes')
    DYNAMODB_ATTEMPTS = os.environ.get('DYNAMODB_ATTEMPTS', 'phishing-app-prod-attempts')
    DYNAMODB_RESPONSES = os.environ.get('DYNAMODB_RESPONSES', 'phishing-app-prod-responses')
    DYNAMODB_INSPECTOR = os.environ.get('DYNAMODB_INSPECTOR', 'phishing-app-prod-inspector-attempts')
    DYNAMODB_INSPECTOR_ANON = os.environ.get(
        'DYNAMODB_INSPECTOR_ANON',
        'phishing-app-prod-inspector-attempts-anon',
    )

    # S3
    S3_BUCKET = os.environ.get('S3_BUCKET', 'phishing-app-prod-eu-west-3')

    # DynamoDB Local (for local development)
    DYNAMODB_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', None)
    S3_ENDPOINT = os.environ.get('S3_ENDPOINT', None)
