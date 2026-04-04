"""Registration worker Lambda — processes SQS registration messages.

Flow:
  1. Receive SQS message with {username, email, password_hash, cohort fields}
  2. Write user to DynamoDB (idempotent: skip if username already exists)
  3. Send SES confirmation email to the student
  4. Publish to SNS registration topic for optional downstream fan-out
"""

import json
import logging
import os

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION_NAME', 'eu-west-3'))
_ses = boto3.client('ses', region_name=os.environ.get('AWS_REGION_NAME', 'eu-west-3'))
_sns = boto3.client('sns', region_name=os.environ.get('AWS_REGION_NAME', 'eu-west-3'))

USERS_TABLE = os.environ['DYNAMODB_USERS']
SES_FROM = os.environ.get('SES_FROM_EMAIL', '')
LOGIN_URL = os.environ.get('APP_LOGIN_URL', '')
SNS_ARN = os.environ.get('SNS_REGISTRATION_ARN', '')


def handler(event, context):
    for record in event.get('Records', []):
        try:
            body = json.loads(record['body'])
            _process_registration(body)
        except Exception:
            logger.exception('Failed to process registration record: %s', record.get('messageId'))
            raise  # Re-raise so SQS retries / DLQ kicks in


def _process_registration(data):
    username = data['username']
    email = data['email']
    password_hash = data['password_hash']

    table = _dynamodb.Table(USERS_TABLE)

    # Idempotency check — skip if username already exists
    resp = table.get_item(Key={'username': username})
    if resp.get('Item'):
        logger.info('User %s already exists, skipping', username)
        return

    # Check email uniqueness via GSI
    email_resp = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(email),
    )
    if email_resp.get('Items'):
        logger.info('Email %s already registered, skipping', email)
        return

    from datetime import datetime, timezone

    role = data.get('role', 'student').lower()
    if role not in ('student', 'admin', 'instructor'):
        role = 'student'

    item = {
        'username': username,
        'email': email,
        'password_hash': password_hash,
        'role': role,
        'group': data.get('group', 'default'),
        'quiz_completed': False,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'class_name': data.get('class_name', 'unknown'),
        'academic_year': data.get('academic_year', 'unknown'),
        'major': data.get('major', 'unknown'),
        'facility': data.get('facility', 'unknown'),
    }

    table.put_item(
        Item=item,
        ConditionExpression='attribute_not_exists(username)',
    )
    logger.info('Created user %s', username)

    _send_confirmation_email(username, email)
    _publish_event(username, email)


def _send_confirmation_email(username, email):
    if not SES_FROM or not email:
        logger.warning('SES_FROM_EMAIL not set or email missing; skipping confirmation email')
        return

    subject = 'Your En Garde account is ready'
    body_text = (
        f'Hello {username},\n\n'
        f'Your En Garde phishing-awareness training account has been created.\n\n'
        f'Username: {username}\n'
        f'Login: {LOGIN_URL}\n\n'
        f'Please log in and change your password at your earliest convenience.\n\n'
        f'En Garde Team'
    )
    body_html = f"""
    <html><body>
    <p>Hello <strong>{username}</strong>,</p>
    <p>Your <strong>En Garde</strong> phishing-awareness training account is ready.</p>
    <ul>
      <li><strong>Username:</strong> {username}</li>
      <li><strong>Login:</strong> <a href="{LOGIN_URL}">{LOGIN_URL}</a></li>
    </ul>
    <p>Please log in and change your password at your earliest convenience.</p>
    <p>En Garde Team</p>
    </body></html>
    """

    try:
        _ses.send_email(
            Source=SES_FROM,
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                    'Html': {'Data': body_html, 'Charset': 'UTF-8'},
                },
            },
        )
        logger.info('Sent confirmation email to %s', email)
    except Exception:
        logger.exception('Failed to send confirmation email to %s', email)
        # Non-fatal — user is already created; do not re-raise


def _publish_event(username, email):
    if not SNS_ARN:
        return
    try:
        _sns.publish(
            TopicArn=SNS_ARN,
            Subject='New user registered',
            Message=json.dumps({'username': username, 'email': email}),
        )
    except Exception:
        logger.exception('Failed to publish registration SNS event for %s', username)
