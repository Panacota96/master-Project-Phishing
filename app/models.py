"""DynamoDB data access layer — replaces SQLAlchemy models."""

import json
import re
import time
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from boto3.dynamodb.conditions import Attr, Key
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


ADMIN_ROLES = ('admin', 'instructor')


# ─── Helper ───────────────────────────────────────────────────────────────────

def _get_table(name_config_key):
    """Return a DynamoDB Table resource for the given config key."""
    return current_app.dynamodb.Table(current_app.config[name_config_key])


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _paginated_scan(table, **kwargs):
    """Scan a DynamoDB table handling pagination via LastEvaluatedKey.

    Accepts the same keyword arguments as table.scan() (e.g. FilterExpression,
    ProjectionExpression, Select, etc.).  Returns a list of all matching items,
    or an integer total when Select='COUNT' is passed.
    """
    is_count = kwargs.get('Select') == 'COUNT'
    items = []
    total = 0
    last_key = None
    while True:
        if last_key:
            kwargs['ExclusiveStartKey'] = last_key
        resp = table.scan(**kwargs)
        if is_count:
            total += resp.get('Count', 0)
        else:
            items.extend(resp.get('Items', []))
        last_key = resp.get('LastEvaluatedKey')
        if not last_key:
            break
    return total if is_count else items


def _redis_client():
    return getattr(current_app, 'redis_client', None)


def _normalize_role(role, fallback='student'):
    normalized = (role or '').strip().lower() or fallback
    if normalized not in ('student', 'admin', 'instructor'):
        return fallback
    return normalized


# ─── Shared cache + configuration helpers ─────────────────────────────────────

def get_threat_cache():
    """Return cached threat feed data from DynamoDB if configured, else None."""
    redis_client = _redis_client()
    if redis_client:
        try:
            raw = redis_client.get('threat:openphish')
            if raw:
                return json.loads(raw)
        except Exception:
            current_app.logger.warning('Redis threat cache lookup failed; falling back to DynamoDB.')

    table_name = current_app.config.get('DYNAMODB_THREAT_CACHE')
    if table_name:
        try:
            table = current_app.dynamodb.Table(table_name)
            resp = table.get_item(Key={'cache_key': 'openphish'})
            item = resp.get('Item')
            if not item:
                return None
            ttl = item.get('ttl')
            if ttl and time.time() > float(ttl):
                return None
            return item.get('data')
        except Exception:
            return None
    return None


def set_threat_cache(data):
    """Persist threat feed data with TTL when the table is configured."""
    ttl_seconds = int(current_app.config.get('THREAT_CACHE_TTL_SECONDS', 3600))
    redis_client = _redis_client()
    if redis_client:
        try:
            redis_client.setex('threat:openphish', ttl_seconds, json.dumps(data))
            redis_client.publish('threat-feed', json.dumps(data))
        except Exception:
            current_app.logger.warning('Redis threat cache write failed; continuing with DynamoDB fallback.')

    table_name = current_app.config.get('DYNAMODB_THREAT_CACHE')
    if not table_name:
        return
    try:
        ttl = int(time.time()) + ttl_seconds
        table = current_app.dynamodb.Table(table_name)
        table.put_item(Item={'cache_key': 'openphish', 'data': data, 'ttl': ttl})
    except Exception:
        current_app.logger.warning('Failed to persist threat cache; continuing with in-memory cache.')


def create_campaign(cohort, filters, status='queued', scheduled=False):
    table_name = current_app.config.get('DYNAMODB_CAMPAIGNS')
    if not table_name:
        return None
    table = _get_table('DYNAMODB_CAMPAIGNS')
    campaign_id = str(uuid4())
    now = _now_iso()
    item = {
        'campaign_id': campaign_id,
        'cohort': cohort,
        'filters': filters,
        'status': status,
        'scheduled': scheduled,
        'created_at': now,
        'updated_at': now,
        'sent_count': 0,
    }
    table.put_item(Item=item)
    return item


def update_campaign_status(campaign_id, status, extra_updates=None):
    table_name = current_app.config.get('DYNAMODB_CAMPAIGNS')
    if not table_name:
        return
    table = _get_table('DYNAMODB_CAMPAIGNS')
    expression = ['SET #status = :status', '#updated_at = :updated']
    values = {':status': status, ':updated': _now_iso()}
    names = {'#status': 'status', '#updated_at': 'updated_at'}
    if extra_updates:
        for key, value in extra_updates.items():
            names[f"#{key}"] = key
            values[f":{key}"] = value
            expression.append(f"#{key} = :{key}")
    try:
        table.update_item(
            Key={'campaign_id': campaign_id},
            UpdateExpression=', '.join(expression),
            ExpressionAttributeValues=values,
            ExpressionAttributeNames=names,
        )
    except Exception:
        current_app.logger.warning('Failed to update campaign %s', campaign_id)


def get_campaign(campaign_id):
    table_name = current_app.config.get('DYNAMODB_CAMPAIGNS')
    if not table_name:
        return None
    try:
        table = _get_table('DYNAMODB_CAMPAIGNS')
        resp = table.get_item(Key={'campaign_id': campaign_id})
        return resp.get('Item')
    except Exception:
        return None


def list_campaigns(limit=50):
    table_name = current_app.config.get('DYNAMODB_CAMPAIGNS')
    if not table_name:
        return []
    table = _get_table('DYNAMODB_CAMPAIGNS')
    items = _paginated_scan(table)
    items_sorted = sorted(items, key=lambda i: i.get('created_at', ''), reverse=True)
    return items_sorted[:limit]


def record_campaign_event(campaign_id, event_type, detail=None):
    table_name = current_app.config.get('DYNAMODB_CAMPAIGN_EVENTS')
    if not table_name:
        return
    table = _get_table('DYNAMODB_CAMPAIGN_EVENTS')
    event_id = f"{_now_iso()}#{uuid4()}"
    item = {
        'campaign_id': campaign_id,
        'event_id': event_id,
        'event_type': event_type,
        'timestamp': _now_iso(),
    }
    if detail:
        item.update(detail)
    try:
        table.put_item(Item=item)
    except Exception:
        current_app.logger.warning('Failed to record campaign event %s', event_type)


def list_campaign_events(campaign_id):
    table_name = current_app.config.get('DYNAMODB_CAMPAIGN_EVENTS')
    if not table_name:
        return []
    table = _get_table('DYNAMODB_CAMPAIGN_EVENTS')
    try:
        resp = table.query(
            KeyConditionExpression=Key('campaign_id').eq(campaign_id),
            ScanIndexForward=False,
        )
        return resp.get('Items', [])
    except Exception:
        return []


def find_users_by_filters(filters):
    """Return users matching cohort filters; fallback to full scan."""
    table = _get_table('DYNAMODB_USERS')
    filter_expr = None
    for key in ('class_name', 'academic_year', 'major', 'facility', 'group'):
        val = filters.get(key)
        if val and val != 'All':
            clause = Attr(key).eq(val)
            filter_expr = clause if filter_expr is None else filter_expr & clause

    if filter_expr is None:
        return [User.from_dynamo(item) for item in _paginated_scan(table)]

    resp = table.scan(FilterExpression=filter_expr)
    return [User.from_dynamo(item) for item in resp.get('Items', [])]


def _cohort_key(class_name, academic_year, major, facility, group):
    return f"{class_name}|{academic_year}|{major}|{facility}|{group}"


def get_inspector_config_for_cohort(class_name, academic_year, major, facility, group):
    """Fetch cohort-specific inspector configuration from DynamoDB or memory."""
    cache = current_app.extensions.setdefault('inspector_cohort_config', {})
    key = _cohort_key(class_name, academic_year, major, facility, group)

    if key in cache:
        return cache[key]

    table_name = current_app.config.get('DYNAMODB_INSPECTOR_CONFIG')
    if table_name:
        try:
            table = current_app.dynamodb.Table(table_name)
            resp = table.get_item(Key={'cohort_key': key})
            item = resp.get('Item')
            if item:
                cache[key] = item
                return item
        except Exception:
            current_app.logger.warning('Falling back to in-memory inspector config.')

    # Defaults mirror the legacy behavior: pool of 8, up to 3 spam, ~35% spam mix
    default_config = {
        'pool_size': current_app.config.get('INSPECTOR_POOL_SIZE_DEFAULT', 8),
        'max_spam': current_app.config.get('INSPECTOR_MAX_SPAM_DEFAULT', 3),
        'spam_ratio': current_app.config.get('INSPECTOR_SPAM_RATIO_DEFAULT', 0.35),
        'targets': [],
    }
    cache[key] = default_config
    return default_config


def save_inspector_config_for_cohort(class_name, academic_year, major, facility, group, config):
    cache = current_app.extensions.setdefault('inspector_cohort_config', {})
    key = _cohort_key(class_name, academic_year, major, facility, group)
    cache[key] = config

    table_name = current_app.config.get('DYNAMODB_INSPECTOR_CONFIG')
    if not table_name:
        return config

    try:
        table = current_app.dynamodb.Table(table_name)
        item = {}
        for k, v in config.items():
            # DynamoDB does not accept Python floats; convert to Decimal
            item[k] = Decimal(str(v)) if isinstance(v, float) else v
        item['cohort_key'] = key
        table.put_item(Item=item)
    except Exception:
        current_app.logger.warning('Unable to persist inspector cohort config; using in-memory cache only.')
    return config


# ─── User "model" (works with Flask-Login) ────────────────────────────────────

class User(UserMixin):
    """In-memory user object hydrated from DynamoDB."""

    def __init__(
        self,
        username,
        email,
        password_hash,
        role='student',
        group='default',
        quiz_completed=False,
        created_at=None,
        class_name='unknown',
        academic_year='unknown',
        major='unknown',
        facility='unknown',
        is_admin=None,  # legacy flag (pre-RBAC); preserved for backwards compatibility
    ):
        resolved_role = _normalize_role(role)
        if is_admin is not None:
            resolved_role = 'admin' if is_admin else 'student'

        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = resolved_role
        self.group = group
        self.quiz_completed = quiz_completed
        self.created_at = created_at or _now_iso()
        self.class_name = class_name
        self.academic_year = academic_year
        self.major = major
        self.facility = facility

    # Flask-Login requires get_id(); we use username as the identifier
    def get_id(self):
        return self.username

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    @property
    def is_admin(self):
        """Legacy boolean: true for admin or instructor (dashboard access)."""
        return self.role in ADMIN_ROLES

    @property
    def is_instructor(self):
        return self.role == 'instructor'

    @property
    def has_admin_access(self):
        return self.role in ADMIN_ROLES

    def to_dynamo(self):
        return {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role,
            'group': self.group,
            'quiz_completed': self.quiz_completed,
            'created_at': self.created_at,
            'class_name': self.class_name,
            'academic_year': self.academic_year,
            'major': self.major,
            'facility': self.facility,
        }

    @classmethod
    def from_dynamo(cls, item):
        if not item:
            return None
        return cls(
            username=item['username'],
            email=item['email'],
            password_hash=item['password_hash'],
            role=_normalize_role(
                item.get('role') or ('admin' if item.get('is_admin') else 'student')
            ),
            group=item.get('group', 'default'),
            quiz_completed=item.get('quiz_completed', False),
            created_at=item.get('created_at'),
            class_name=item.get('class_name', 'unknown'),
            academic_year=item.get('academic_year', 'unknown'),
            major=item.get('major', 'unknown'),
            facility=item.get('facility', 'unknown'),
        )


# ─── User CRUD ────────────────────────────────────────────────────────────────

def get_user(username):
    table = _get_table('DYNAMODB_USERS')
    resp = table.get_item(Key={'username': username})
    return User.from_dynamo(resp.get('Item'))


def get_user_by_email(email):
    table = _get_table('DYNAMODB_USERS')
    resp = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(email),
    )
    items = resp.get('Items', [])
    return User.from_dynamo(items[0]) if items else None


def delete_user(username):
    """Remove a user from DynamoDB."""
    table = _get_table('DYNAMODB_USERS')
    table.delete_item(Key={'username': username})
    return True


def create_user(
    username,
    email,
    password,
    role='student',
    group='default',
    class_name='unknown',
    academic_year='unknown',
    major='unknown',
    facility='unknown',
):
    table = _get_table('DYNAMODB_USERS')
    role = _normalize_role(role)
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
        group=group,
        class_name=class_name,
        academic_year=academic_year,
        major=major,
        facility=facility,
    )
    from botocore.exceptions import ClientError
    try:
        table.put_item(
            Item=user.to_dynamo(),
            ConditionExpression=Attr('username').not_exists(),
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ValueError(f"Username '{username}' already exists.")
        raise
    return user


def batch_create_users(users_list):
    """Write multiple users to DynamoDB in batch.
    users_list: list of dicts with keys username, email, password, role (optional),
    group, class_name, academic_year, major, facility.
    Returns (created_count, skipped_usernames).
    """
    table = _get_table('DYNAMODB_USERS')
    created = 0
    skipped = []

    with table.batch_writer() as batch:
        for u in users_list:
            # Skip if user already exists
            existing = get_user(u['username'])
            if existing:
                skipped.append(u['username'])
                continue
            existing_email = get_user_by_email(u['email'])
            if existing_email:
                skipped.append(u['username'])
                continue

            user = User(
                username=u['username'],
                email=u['email'],
                password_hash=generate_password_hash(u['password']),
                role=_normalize_role(u.get('role', 'student')),
                group=u.get('group', 'default'),
                class_name=u.get('class_name', 'unknown'),
                academic_year=u.get('academic_year', 'unknown'),
                major=u.get('major', 'unknown'),
                facility=u.get('facility', 'unknown'),
            )
            batch.put_item(Item=user.to_dynamo())
            created += 1

    return created, skipped


def list_users_by_group(group):
    table = _get_table('DYNAMODB_USERS')
    resp = table.query(
        IndexName='group-index',
        KeyConditionExpression=Key('group').eq(group),
    )
    return [User.from_dynamo(item) for item in resp.get('Items', [])]


def list_all_users():
    table = _get_table('DYNAMODB_USERS')
    return [User.from_dynamo(item) for item in _paginated_scan(table)]


def count_users():
    table = _get_table('DYNAMODB_USERS')
    return _paginated_scan(table, Select='COUNT')


def get_distinct_groups():
    """Return a sorted list of unique group names."""
    users = list_all_users()
    return sorted({u.group for u in users})


def get_distinct_cohorts():
    """Return a sorted list of unique cohort triples (class, academic_year, major)."""
    users = list_all_users()
    cohorts = {(u.class_name, u.academic_year, u.major) for u in users}
    return sorted(cohorts)


def get_distinct_facilities():
    """Return a sorted list of unique facility names."""
    users = list_all_users()
    return sorted({u.facility for u in users})


def mark_quiz_completed(username):
    table = _get_table('DYNAMODB_USERS')
    table.update_item(
        Key={'username': username},
        UpdateExpression='SET quiz_completed = :val',
        ExpressionAttributeValues={':val': True},
    )


def update_user_password(username, new_password):
    """Update a user's password hash."""
    table = _get_table('DYNAMODB_USERS')
    table.update_item(
        Key={'username': username},
        UpdateExpression='SET password_hash = :val',
        ExpressionAttributeValues={':val': generate_password_hash(new_password)},
    )


def update_user_role(username, role):
    """Update a user's role (student/instructor/admin)."""
    normalized = _normalize_role(role)
    table = _get_table('DYNAMODB_USERS')
    table.update_item(
        Key={'username': username},
        UpdateExpression='SET #r = :role',
        ExpressionAttributeNames={'#r': 'role'},
        ExpressionAttributeValues={':role': normalized},
    )


def get_user_inspector_state(username):
    table = _get_table('DYNAMODB_USERS')
    resp = table.get_item(Key={'username': username})
    item = resp.get('Item') or {}
    return {
        'submitted': item.get('inspector_submitted', []) or [],
        'locked': bool(item.get('inspector_locked', False)),
    }


def update_user_inspector_state(username, submitted=None, locked=None):
    table = _get_table('DYNAMODB_USERS')
    updates = []
    values = {}
    if submitted is not None:
        updates.append('inspector_submitted = :submitted')
        values[':submitted'] = submitted
    if locked is not None:
        updates.append('inspector_locked = :locked')
        values[':locked'] = locked
    if not updates:
        return
    table.update_item(
        Key={'username': username},
        UpdateExpression=f"SET {', '.join(updates)}",
        ExpressionAttributeValues=values,
    )


def reset_user_inspector_state(username):
    update_user_inspector_state(username, submitted=[], locked=False)


def reset_users_inspector_state(usernames):
    """Reset inspector state for multiple users. Returns count reset."""
    if not usernames:
        return 0
    count = 0
    for username in usernames:
        update_user_inspector_state(username, submitted=[], locked=False)
        count += 1
    return count


# ─── Quiz CRUD ────────────────────────────────────────────────────────────────

def get_quiz(quiz_id):
    table = _get_table('DYNAMODB_QUIZZES')
    resp = table.get_item(Key={'quiz_id': quiz_id})
    return resp.get('Item')


def list_quizzes():
    table = _get_table('DYNAMODB_QUIZZES')
    items = _paginated_scan(table)
    return sorted(items, key=lambda q: q.get('created_at', ''), reverse=True)


def create_quiz(quiz_id, title, description, questions, video_url=None):
    """Create a quiz with embedded questions.
    questions: list of dicts with question_id, question_text, explanation, answers.
    """
    table = _get_table('DYNAMODB_QUIZZES')
    item = {
        'quiz_id': quiz_id,
        'title': title,
        'description': description,
        'questions': questions,
        'created_at': _now_iso(),
    }
    if video_url:
        item['video_url'] = video_url
    table.put_item(Item=item)
    return item


# ─── Attempt CRUD ─────────────────────────────────────────────────────────────

def get_attempt(username, quiz_id):
    table = _get_table('DYNAMODB_ATTEMPTS')
    resp = table.get_item(Key={'username': username, 'quiz_id': quiz_id})
    return resp.get('Item')


def create_attempt(
    username,
    quiz_id,
    score,
    total,
    group='default',
    class_name='unknown',
    academic_year='unknown',
    major='unknown',
    allow_overwrite=False,
    attempt_number=1,
    time_limit_seconds=None,
):
    """Write an attempt. Uses a condition to enforce one attempt per user per quiz unless overwrite is allowed."""
    table = _get_table('DYNAMODB_ATTEMPTS')
    percentage = round((score / total * 100), 1) if total > 0 else Decimal('0')
    item = {
        'username': username,
        'quiz_id': quiz_id,
        'score': score,
        'total': total,
        'percentage': Decimal(str(percentage)),
        'group': group,
        'class_name': class_name,
        'academic_year': academic_year,
        'major': major,
        'completed_at': _now_iso(),
        'attempt_number': attempt_number,
    }
    if time_limit_seconds:
        item['time_limit_seconds'] = time_limit_seconds
    if allow_overwrite:
        table.put_item(Item=item)
        return item
    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(username) AND attribute_not_exists(quiz_id)',
        )
        return item
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return None  # Attempt already exists


def list_attempts_by_quiz(quiz_id):
    table = _get_table('DYNAMODB_ATTEMPTS')
    resp = table.query(
        IndexName='quiz-index',
        KeyConditionExpression=Key('quiz_id').eq(quiz_id),
    )
    return resp.get('Items', [])


def list_attempts_by_group(group):
    table = _get_table('DYNAMODB_ATTEMPTS')
    resp = table.query(
        IndexName='group-index',
        KeyConditionExpression=Key('group').eq(group),
    )
    return resp.get('Items', [])


def list_all_attempts():
    table = _get_table('DYNAMODB_ATTEMPTS')
    return _paginated_scan(table)


def list_attempts_by_user(username):
    table = _get_table('DYNAMODB_ATTEMPTS')
    resp = table.query(
        KeyConditionExpression=Key('username').eq(username),
    )
    return resp.get('Items', [])


# ─── Response CRUD ────────────────────────────────────────────────────────────

def save_response(username, quiz_id, question_id, selected_answer_id, is_correct):
    table = _get_table('DYNAMODB_RESPONSES')
    item = {
        'username_quiz_id': f'{username}#{quiz_id}',
        'question_id': question_id,
        'selected_answer_id': selected_answer_id,
        'is_correct': is_correct,
        'username': username,
        'quiz_question_id': f'{quiz_id}#{question_id}',
        'answered_at': _now_iso(),
    }
    table.put_item(Item=item)
    return item


def get_responses(username, quiz_id):
    table = _get_table('DYNAMODB_RESPONSES')
    resp = table.query(
        KeyConditionExpression=Key('username_quiz_id').eq(f'{username}#{quiz_id}'),
    )
    return resp.get('Items', [])


def get_responses_by_question(quiz_id, question_id):
    """Get all responses for a specific question across all users."""
    table = _get_table('DYNAMODB_RESPONSES')
    resp = table.query(
        IndexName='quiz-question-index',
        KeyConditionExpression=Key('quiz_question_id').eq(f'{quiz_id}#{question_id}'),
    )
    return resp.get('Items', [])


# ─── Inspector Attempt CRUD ──────────────────────────────────────────────────

def create_inspector_attempt(
    username,
    group,
    email_file,
    classification,
    selected_signals,
    expected_classification,
    expected_signals,
    is_correct,
    class_name='unknown',
    academic_year='unknown',
    major='unknown',
):
    table = _get_table('DYNAMODB_INSPECTOR')
    item = {
        'username': username,
        'submitted_at': _now_iso(),
        'group': group,
        'email_file': email_file,
        'classification': classification,
        'selected_signals': selected_signals,
        'expected_classification': expected_classification,
        'expected_signals': expected_signals,
        'is_correct': is_correct,
        'class_name': class_name,
        'academic_year': academic_year,
        'major': major,
    }
    table.put_item(Item=item)
    return item


def list_inspector_attempts():
    table = _get_table('DYNAMODB_INSPECTOR')
    return _paginated_scan(table)


def list_inspector_attempts_by_group(group):
    table = _get_table('DYNAMODB_INSPECTOR')
    resp = table.query(
        IndexName='group-index',
        KeyConditionExpression=Key('group').eq(group),
    )
    return resp.get('Items', [])


def list_inspector_attempts_by_email(email_file):
    table = _get_table('DYNAMODB_INSPECTOR')
    resp = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email_file').eq(email_file),
    )
    return resp.get('Items', [])


def count_inspector_attempts():
    table = _get_table('DYNAMODB_INSPECTOR')
    return _paginated_scan(table, Select='COUNT')


# ─── Inspector Attempt CRUD (Anonymous) ───────────────────────────────────────

def create_inspector_attempt_anonymous(
    email_file,
    classification,
    selected_signals,
    expected_classification,
    expected_signals,
    is_correct,
    class_name='unknown',
    academic_year='unknown',
    major='unknown',
    facility='unknown',
    explanation_rating=None,
):
    table = _get_table('DYNAMODB_INSPECTOR_ANON')
    item = {
        'attempt_id': str(uuid4()),
        'submitted_at': _now_iso(),
        'email_file': email_file,
        'classification': classification,
        'selected_signals': selected_signals,
        'expected_classification': expected_classification,
        'expected_signals': expected_signals,
        'is_correct': is_correct,
        'class_name': class_name,
        'academic_year': academic_year,
        'major': major,
        'facility': facility,
    }
    if explanation_rating is not None:
        item['explanation_rating'] = explanation_rating
    table.put_item(Item=item)
    return item


def list_inspector_attempts_anonymous():
    table = _get_table('DYNAMODB_INSPECTOR_ANON')
    return _paginated_scan(table)


def list_inspector_attempts_anonymous_by_email(email_file):
    attempts = list_inspector_attempts_anonymous()
    return [a for a in attempts if a.get('email_file') == email_file]


def count_inspector_attempts_anonymous():
    table = _get_table('DYNAMODB_INSPECTOR_ANON')
    return _paginated_scan(table, Select='COUNT')


# ─── Answer Key Overrides ────────────────────────────────────────────────────

def get_answer_key_overrides():
    """Return all admin-written answer key overrides keyed by email_file.

    Returns an empty dict if the table does not exist yet (e.g. before the
    first Terraform apply that creates DYNAMODB_ANSWER_KEY_OVERRIDES).
    """
    try:
        table = _get_table('DYNAMODB_ANSWER_KEY_OVERRIDES')
        return {item['email_file']: item for item in _paginated_scan(table)}
    except Exception as e:
        # Table may not exist yet in this environment; fall back to empty overrides
        current_app.logger.warning('get_answer_key_overrides: %s', e)
        return {}


VALID_SIGNALS = frozenset([
    'impersonation', 'punycode', 'externaldomain', 'spoof',
    'socialeng', 'urgency', 'fakeinvoice', 'attachment', 'fakelogin', 'sidechannel',
])
VALID_CLASSIFICATIONS = frozenset(['Phishing', 'Spam'])


def _normalize_signals(signals):
    """Return a deduplicated list of lowercase-alphanumeric signal names."""
    seen = set()
    result = []
    for s in (signals or []):
        normalized = re.sub(r'[^a-z0-9]', '', str(s).lower())
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def get_effective_answer_key():
    """Merge static ANSWER_KEY with DynamoDB overrides (overrides win).

    Signals in the merged result are guaranteed to be lowercase and
    deduplicated so that comparisons against user-submitted signals are
    consistent regardless of how the override was stored.
    """
    from app.inspector.answer_key import ANSWER_KEY
    overrides = get_answer_key_overrides()
    merged = {}
    for email_file, entry in ANSWER_KEY.items():
        merged[email_file] = {
            'classification': entry['classification'],
            'signals': _normalize_signals(entry.get('signals', [])),
            'explanation': entry.get('explanation', ''),
        }
    for email_file, override in overrides.items():
        merged[email_file] = {
            'classification': override['classification'],
            'signals': _normalize_signals(override.get('signals', [])),
            'explanation': override.get('explanation', ''),
        }
    return merged


def set_answer_key_override(email_file, classification, signals, explanation=''):
    """Write or update an admin override for an email's answer key entry.

    Raises ValueError for unknown classification or signal names so that
    callers get immediate feedback instead of storing invalid data.
    """
    if classification not in VALID_CLASSIFICATIONS:
        raise ValueError(
            f"Invalid classification '{classification}'. Must be one of {sorted(VALID_CLASSIFICATIONS)}."
        )
    normalized = _normalize_signals(signals)
    unknown = [s for s in normalized if s not in VALID_SIGNALS]
    if unknown:
        raise ValueError(
            f"Unknown signal(s): {unknown}. Valid signals: {sorted(VALID_SIGNALS)}."
        )
    table = _get_table('DYNAMODB_ANSWER_KEY_OVERRIDES')
    table.put_item(Item={
        'email_file': email_file,
        'classification': classification,
        'signals': normalized,
        'explanation': str(explanation),
    })


def delete_answer_key_override(email_file):
    """Remove an override, reverting to the static answer_key.py baseline."""
    table = _get_table('DYNAMODB_ANSWER_KEY_OVERRIDES')
    table.delete_item(Key={'email_file': email_file})


# ─── Cohort Token CRUD ────────────────────────────────────────────────────────

def create_cohort_token(token, class_name, academic_year, major, facility, created_by):
    """Write a new cohort token. Expires after 90 days (TTL via DynamoDB)."""
    import time
    table = _get_table('DYNAMODB_COHORT_TOKENS')
    item = {
        'token': token,
        'class_name': class_name,
        'academic_year': academic_year,
        'major': major,
        'facility': facility,
        'created_by': created_by,
        'created_at': _now_iso(),
        'expires_at': int(time.time()) + 90 * 24 * 3600,
    }
    table.put_item(Item=item)
    return item


def get_cohort_token(token):
    """Return the cohort token item or None if not found / expired."""
    import time
    table = _get_table('DYNAMODB_COHORT_TOKENS')
    resp = table.get_item(Key={'token': token})
    item = resp.get('Item')
    if not item:
        return None
    # Guard against DynamoDB TTL not having deleted the item yet
    if int(item.get('expires_at', 0)) < int(time.time()):
        return None
    return item


# ─── SQS Registration Enqueue ─────────────────────────────────────────────────

def enqueue_registration(sqs_client, queue_url, data):
    """Send a registration message to the SQS queue.

    data: dict with username, email, password_hash, class_name, academic_year,
          major, facility, group.
    Returns the SQS SendMessage response.
    """
    import json
    return sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(data),
    )


# ─── Bug Report CRUD ─────────────────────────────────────────────────────────

def create_bug_report(username, description, page_url):
    """Create a new bug report entry in DynamoDB."""
    table = _get_table('DYNAMODB_BUGS')
    item = {
        'bug_id': str(uuid4()),
        'submitted_at': _now_iso(),
        'username': username,
        'description': description,
        'page_url': page_url,
        'status': 'Open',
    }
    table.put_item(Item=item)
    return item


def list_bug_reports():
    """List all bug reports from DynamoDB."""
    table = _get_table('DYNAMODB_BUGS')
    items = _paginated_scan(table)
    return sorted(items, key=lambda x: x.get('submitted_at', ''), reverse=True)
