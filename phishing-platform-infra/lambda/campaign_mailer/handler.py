"""Campaign mailer Lambda — fan-out phishing simulation emails via SES.

Flow:
 1. Triggered by SQS (admin launch or scheduled)
 2. Resolves target users from DynamoDB cohorts/groups
 3. Sends SES emails per user
 4. Records delivery events in DynamoDB + Redis pub/sub channel
"""

import json
import logging
import os
from uuid import uuid4
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Attr, Key
import redis

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

AWS_REGION = os.environ.get('AWS_REGION_NAME', 'eu-west-3')
USERS_TABLE = os.environ['DYNAMODB_USERS']
CAMPAIGNS_TABLE = os.environ['DYNAMODB_CAMPAIGNS']
CAMPAIGN_EVENTS_TABLE = os.environ['DYNAMODB_CAMPAIGN_EVENTS']
SES_FROM = os.environ.get('SES_FROM_EMAIL', '')

_dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
_ses = boto3.client('ses', region_name=AWS_REGION)

_redis_client = None
_redis_endpoint = os.environ.get('REDIS_ENDPOINT') or os.environ.get('REDIS_URL')
if _redis_endpoint:
    scheme = 'rediss' if os.environ.get('REDIS_USE_TLS', 'false').lower() == 'true' else 'redis'
    if '://' not in _redis_endpoint:
        _redis_endpoint = f"{scheme}://{_redis_endpoint}"
    try:
        _redis_client = redis.Redis.from_url(_redis_endpoint)
    except Exception:
        logger.warning('Redis client unavailable; proceeding without pub/sub')


def handler(event, context):
    for record in event.get('Records', []):
        try:
            payload = json.loads(record['body'])
            _process_campaign(payload)
        except Exception:
            logger.exception('Failed to process campaign record: %s', record.get('messageId'))
            raise


def _process_campaign(payload):
    campaign_id = payload.get('campaign_id') or str(uuid4())
    filters = payload.get('filters') or {}
    scheduled = payload.get('scheduled', False)

    campaign = _ensure_campaign(campaign_id, filters, scheduled)
    _update_campaign_status(campaign_id, 'sending')
    targets = _fetch_targets(filters)
    logger.info('Campaign %s targeting %d users', campaign_id, len(targets))

    sent = 0
    for user in targets:
        try:
            _send_email(user, campaign_id)
            sent += 1
        except Exception:
            logger.exception('Failed to send campaign email to %s', user.get('email'))
            _record_event(campaign_id, 'send_failed', {'email': user.get('email')})

    _update_campaign_status(campaign_id, 'sent', {'sent_count': sent, 'completed_at': _now_iso()})
    _record_event(campaign_id, 'sent', {'recipients': sent})
    _publish({'type': 'campaign_sent', 'campaign_id': campaign_id, 'recipients': sent})


def _ensure_campaign(campaign_id, filters, scheduled=False):
    table = _dynamodb.Table(CAMPAIGNS_TABLE)
    cohort = _cohort_label(filters)
    now = _now_iso()
    item = {
        'campaign_id': campaign_id,
        'cohort': cohort,
        'filters': filters,
        'status': 'queued',
        'scheduled': scheduled,
        'created_at': now,
        'updated_at': now,
        'sent_count': 0,
    }
    table.put_item(Item=item)
    return item


def _fetch_targets(filters):
    table = _dynamodb.Table(USERS_TABLE)
    filter_expr = None
    for key in ('class_name', 'academic_year', 'major', 'facility', 'group'):
        val = filters.get(key)
        if val and val != 'All':
            clause = Attr(key).eq(val)
            filter_expr = clause if filter_expr is None else filter_expr & clause

    if filter_expr is None:
        resp_items = table.scan().get('Items', [])
    else:
        resp_items = table.scan(FilterExpression=filter_expr).get('Items', [])
    return resp_items


def _send_email(user, campaign_id):
    if not SES_FROM:
        logger.warning('SES_FROM_EMAIL missing; skipping send.')
        return

    subject = 'Phishing simulation'
    login_hint = os.environ.get('APP_LOGIN_URL', '')
    body_text = (
        f"Hello {user.get('username')},\n\n"
        "You have been enrolled in a phishing simulation exercise. "
        "Please watch out for suspicious emails and report anything unusual.\n\n"
        f"Login: {login_hint}\n"
        "— En Garde Training"
    )
    body_html = f"""
    <html><body>
    <p>Hello <strong>{user.get('username')}</strong>,</p>
    <p>You have been enrolled in a phishing simulation exercise. Please watch out for suspicious emails and report anything unusual.</p>
    <p><a href="{login_hint}">Training portal</a></p>
    <p>— En Garde Training</p>
    </body></html>
    """
    _ses.send_email(
        Source=SES_FROM,
        Destination={'ToAddresses': [user.get('email')]},
        Message={
            'Subject': {'Data': subject, 'Charset': 'UTF-8'},
            'Body': {
                'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                'Html': {'Data': body_html, 'Charset': 'UTF-8'},
            },
        },
    )
    _record_event(campaign_id, 'sent_user', {'email': user.get('email'), 'username': user.get('username')})


def _record_event(campaign_id, event_type, detail=None):
    table = _dynamodb.Table(CAMPAIGN_EVENTS_TABLE)
    event_id = f"{_now_iso()}#{uuid4()}"
    item = {
        'campaign_id': campaign_id,
        'event_id': event_id,
        'event_type': event_type,
        'timestamp': _now_iso(),
    }
    if detail:
        item.update(detail)
    table.put_item(Item=item)


def _update_campaign_status(campaign_id, status, extra=None):
    table = _dynamodb.Table(CAMPAIGNS_TABLE)
    updates = {
        '#status': 'status',
        '#updated': 'updated_at',
    }
    values = {
        ':status': status,
        ':updated': _now_iso(),
    }
    expression = ['#status = :status', '#updated = :updated']
    if extra:
        for key, val in extra.items():
            updates[f"#{key}"] = key
            values[f":{key}"] = val
            expression.append(f"#{key} = :{key}")
    table.update_item(
        Key={'campaign_id': campaign_id},
        UpdateExpression='SET ' + ', '.join(expression),
        ExpressionAttributeNames=updates,
        ExpressionAttributeValues=values,
    )


def _publish(payload):
    if not _redis_client:
        return
    try:
        _redis_client.publish('campaign-events', json.dumps(payload))
    except Exception:
        logger.warning('Failed to publish campaign event to Redis')


def _cohort_label(filters):
    return "|".join([
        filters.get('class_name', 'All'),
        filters.get('academic_year', 'All'),
        filters.get('major', 'All'),
        filters.get('facility', 'All'),
        filters.get('group', 'All'),
    ])


def _now_iso():
    return datetime.now(timezone.utc).isoformat()
