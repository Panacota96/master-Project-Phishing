"""Create DynamoDB Local tables and seed all quizzes for local Docker dev."""
import os
import boto3

ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8766')
REGION = 'eu-west-3'

dynamodb = boto3.resource(
    'dynamodb',
    region_name=REGION,
    endpoint_url=ENDPOINT,
    aws_access_key_id='fake',
    aws_secret_access_key='fake',
)

TABLES = [
    dict(
        TableName='phishing-app-dev-users',
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
    ),
    dict(
        TableName='phishing-app-dev-quizzes',
        KeySchema=[{'AttributeName': 'quiz_id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'quiz_id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
    ),
    dict(
        TableName='phishing-app-dev-attempts',
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
    ),
    dict(
        TableName='phishing-app-dev-responses',
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
    ),
    dict(
        TableName='phishing-app-dev-inspector-attempts',
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
    ),
    dict(
        TableName='phishing-app-dev-inspector-attempts-anon',
        KeySchema=[
            {'AttributeName': 'attempt_id', 'KeyType': 'HASH'},
            {'AttributeName': 'submitted_at', 'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'attempt_id', 'AttributeType': 'S'},
            {'AttributeName': 'submitted_at', 'AttributeType': 'S'},
        ],
        BillingMode='PAY_PER_REQUEST',
    ),
    dict(
        TableName='phishing-app-dev-bugs',
        KeySchema=[{'AttributeName': 'bug_id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'bug_id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
    ),
    dict(
        TableName='phishing-app-dev-answer-key-overrides',
        KeySchema=[{'AttributeName': 'email_file', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'email_file', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
    ),
]

existing = {t.name for t in dynamodb.tables.all()}

for table_def in TABLES:
    name = table_def['TableName']
    if name in existing:
        print(f'  - Table already exists, skipping: {name}')
    else:
        dynamodb.create_table(**table_def)
        print(f'  - Created table: {name}')

print('Tables ready.')
