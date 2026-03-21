"""DynamoDB data access layer — replaces SQLAlchemy models."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from boto3.dynamodb.conditions import Key
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


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


# ─── User "model" (works with Flask-Login) ────────────────────────────────────

class User(UserMixin):
    """In-memory user object hydrated from DynamoDB."""

    def __init__(self, username, email, password_hash, is_admin=False,
                 group='default', quiz_completed=False, created_at=None,
                 class_name='unknown', academic_year='unknown', major='unknown',
                 facility='unknown'):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
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

    def to_dynamo(self):
        return {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'is_admin': self.is_admin,
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
            is_admin=item.get('is_admin', False),
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
    is_admin=False,
    group='default',
    class_name='unknown',
    academic_year='unknown',
    major='unknown',
    facility='unknown',
):
    table = _get_table('DYNAMODB_USERS')
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        is_admin=is_admin,
        group=group,
        class_name=class_name,
        academic_year=academic_year,
        major=major,
        facility=facility,
    )
    table.put_item(Item=user.to_dynamo())
    return user


def batch_create_users(users_list):
    """Write multiple users to DynamoDB in batch.
    users_list: list of dicts with keys username, email, password, group, class_name,
    academic_year, major, facility.
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
):
    """Write an attempt. Uses a condition to enforce one attempt per user per quiz."""
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
    }
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
    }
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


def get_effective_answer_key():
    """Merge static ANSWER_KEY with DynamoDB overrides (overrides win)."""
    from app.inspector.answer_key import ANSWER_KEY
    overrides = get_answer_key_overrides()
    merged = dict(ANSWER_KEY)
    for email_file, override in overrides.items():
        merged[email_file] = {
            'classification': override['classification'],
            'signals': list(override.get('signals', [])),
            'explanation': override.get('explanation', ''),
        }
    return merged


def set_answer_key_override(email_file, classification, signals, explanation=''):
    """Write or update an admin override for an email's answer key entry."""
    table = _get_table('DYNAMODB_ANSWER_KEY_OVERRIDES')
    table.put_item(Item={
        'email_file': email_file,
        'classification': classification,
        'signals': signals,
        'explanation': explanation,
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
