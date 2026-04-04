# Feature Proposals

**Project:** En Garde — Phishing Awareness Training (ESME)
**Date:** 2026-03-21
**Author:** Claude Sonnet 4.6 (research & design pass)
**Status:** Feature A implemented (2026-04-04). Features B and C remain proposals.

---

## Table of Contents

1. [Feature A: Admin-Side Password Change](#feature-a-admin-side-password-change)
2. [Feature B: AI Integration with Amazon Bedrock](#feature-b-ai-integration-with-amazon-bedrock)
3. [Feature C: UI/UX Improvements](#feature-c-uiux-improvements)
4. [Implementation Order and Dependencies](#implementation-order-and-dependencies)

---

## Feature A: Admin-Side Password Change

### Overview

Admins currently can create and delete users from the dashboard (`/dashboard/users`), but have no way to reset a student's password without deleting and recreating the account. This feature adds a per-user password reset form inside the existing user management table.

The `update_user_password` function **already exists** in `app/models.py` (line 251–258) and is already used by the student's own change-password flow (`app/auth/routes.py`). This feature simply exposes that function to admins through a new dashboard route.

**Effort:** Small (1–2 hours of implementation)

---

### A.1 — Model function (already exists)

`app/models.py` already contains the required function:

```python
def update_user_password(username, new_password):
    """Update a user's password hash."""
    table = _get_table('DYNAMODB_USERS')
    table.update_item(
        Key={'username': username},
        UpdateExpression='SET password_hash = :val',
        ExpressionAttributeValues={':val': generate_password_hash(new_password)},
    )
```

No new model function is needed. The route calls `update_user_password` directly.

---

### A.2 — Form class

Add to `app/dashboard/forms.py` (create this file — `dashboard` blueprint currently has no `forms.py`):

```python
# app/dashboard/forms.py
import re

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, ValidationError


class AdminSetPasswordForm(FlaskForm):
    """Admin form to set a new password for any user.
    Does NOT require the current password — admin privilege bypasses that check.
    """
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords must match.')],
    )
    submit = SubmitField('Set Password')

    def validate_new_password(self, field):
        password = field.data or ''
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters.')
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must include a lowercase letter.')
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must include an uppercase letter.')
        if not re.search(r'\d', password):
            raise ValidationError('Password must include a number.')
        if not re.search(r'[^A-Za-z0-9]', password):
            raise ValidationError('Password must include a symbol.')
```

The password strength rules mirror those in `app/auth/forms.py` (`ChangePasswordForm.validate_new_password` and `_validate_password_strength`), keeping policy consistent.

---

### A.3 — Route

Add to `app/dashboard/routes.py`. The import block at the top already imports `get_user` and `update_user_password` is available from `app.models`; add it to that import list.

```python
# Add to the existing import at the top of app/dashboard/routes.py:
from app.models import (
    # ... existing imports ...
    update_user_password,       # <-- add this
)

# Add this import near the top of the file:
from app.dashboard.forms import AdminSetPasswordForm


@bp.route('/users/<username>/set-password', methods=['GET', 'POST'])
@login_required
def set_user_password(username):
    """Admin-only: set a new password for any user account."""
    if not current_user.is_admin:
        abort(403)

    target_user = get_user(username)
    if not target_user:
        flash(f'User "{username}" not found.', 'danger')
        return redirect(url_for('dashboard.list_users'))

    form = AdminSetPasswordForm()
    if form.validate_on_submit():
        try:
            update_user_password(username, form.new_password.data)
            flash(f'Password for "{username}" has been updated.', 'success')
            return redirect(url_for('dashboard.list_users'))
        except Exception as e:
            current_app.logger.error(f'Failed to set password for {username}: {e}')
            flash('Failed to update password. Please try again.', 'danger')

    return render_template(
        'admin/set_user_password.html',
        form=form,
        target_user=target_user,
    )
```

**URL pattern:** `GET/POST /dashboard/users/<username>/set-password`

The route follows the exact same guard pattern as all other admin routes in `app/dashboard/routes.py`: `@login_required` decorator + `if not current_user.is_admin: abort(403)`.

---

### A.4 — Template

Create `app/templates/admin/set_user_password.html`:

```html
{% extends "base.html" %}
{% block title %}Set Password — {{ target_user.username }}{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 col-lg-5">
        <nav aria-label="breadcrumb" class="mb-3">
            <ol class="breadcrumb">
                <li class="breadcrumb-item">
                    <a href="{{ url_for('dashboard.list_users') }}">Manage Users</a>
                </li>
                <li class="breadcrumb-item active">Set Password</li>
            </ol>
        </nav>

        <div class="card shadow-sm">
            <div class="card-header">
                <h5 class="mb-0">Set Password for <strong>{{ target_user.username }}</strong></h5>
                <small class="text-muted">{{ target_user.email }}</small>
            </div>
            <div class="card-body">
                <div class="alert alert-warning mb-3">
                    <strong>Admin action:</strong> This will immediately change the user's password.
                    The user will need to use the new password on their next login.
                </div>
                <form method="POST">
                    {{ form.hidden_tag() }}
                    <div class="mb-3">
                        {{ form.new_password.label(class="form-label") }}
                        {{ form.new_password(class="form-control") }}
                        <div class="form-text">
                            Minimum 8 characters with uppercase, lowercase, number, and symbol.
                        </div>
                        {% for error in form.new_password.errors %}
                        <div class="text-danger small">{{ error }}</div>
                        {% endfor %}
                    </div>
                    <div class="mb-3">
                        {{ form.confirm_password.label(class="form-label") }}
                        {{ form.confirm_password(class="form-control") }}
                        {% for error in form.confirm_password.errors %}
                        <div class="text-danger small">{{ error }}</div>
                        {% endfor %}
                    </div>
                    <div class="d-flex gap-2">
                        {{ form.submit(class="btn btn-danger") }}
                        <a href="{{ url_for('dashboard.list_users') }}" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

### A.5 — Wire up the button in the existing users table

In `app/templates/admin/users.html`, add a "Set Password" button to the Actions column of each row, next to the existing Delete button:

```html
{# Inside the actions <td> in the users table, alongside the existing delete form: #}
<a href="{{ url_for('dashboard.set_user_password', username=user.username) }}"
   class="btn btn-sm btn-outline-secondary me-1">Set Password</a>
```

The full modified actions cell becomes:

```html
<td class="text-end">
    {% if user.username != current_user.username %}
    <a href="{{ url_for('dashboard.set_user_password', username=user.username) }}"
       class="btn btn-sm btn-outline-secondary me-1">Set Password</a>
    <form action="{{ url_for('dashboard.remove_user', username=user.username) }}"
          method="POST" class="d-inline"
          onsubmit="return confirm('Are you sure you want to delete user {{ user.username }}?');">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <button type="submit" class="btn btn-sm btn-outline-danger">Delete</button>
    </form>
    {% else %}
    <span class="text-muted small">Current User</span>
    {% endif %}
</td>
```

---

### A.6 — Test

Add to `tests/test_dashboard.py` (following the class/method structure already present in that file):

```python
# Add this import at the top of tests/test_dashboard.py:
from app.models import create_user, get_user

class TestAdminSetPassword:
    """Tests for the admin set-password route."""

    def test_set_password_page_renders_for_admin(self, client, seed_admin, seed_user):
        login(client, 'admin', 'admin123')
        resp = client.get('/dashboard/users/testuser/set-password')
        assert resp.status_code == 200
        assert b'Set Password' in resp.data
        assert b'testuser' in resp.data

    def test_set_password_requires_admin(self, client, seed_user, app):
        with app.app_context():
            create_user('victim', 'victim@test.com', 'Pass123!',
                        class_name='Class A', academic_year='2025', major='CS')
        login(client, 'testuser', 'password123')
        resp = client.get('/dashboard/users/victim/set-password')
        assert resp.status_code == 403

    def test_set_password_requires_login(self, client, seed_user):
        resp = client.get('/dashboard/users/testuser/set-password')
        assert resp.status_code in (302, 401)

    def test_set_password_404_on_unknown_user(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.get('/dashboard/users/ghost/set-password',
                          follow_redirects=True)
        assert b'not found' in resp.data

    def test_set_password_updates_hash(self, client, app, seed_admin, seed_user):
        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/users/testuser/set-password',
            data={
                'new_password': 'AdminSet1!',
                'confirm_password': 'AdminSet1!',
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'Password for' in resp.data
        assert b'has been updated' in resp.data

        # Verify the new hash in DynamoDB
        with app.app_context():
            user = get_user('testuser')
            assert user.check_password('AdminSet1!') is True
            assert user.check_password('password123') is False

    def test_set_password_mismatch_fails(self, client, seed_admin, seed_user):
        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/users/testuser/set-password',
            data={
                'new_password': 'AdminSet1!',
                'confirm_password': 'Different1!',
            },
            follow_redirects=True,
        )
        # Form validation error — stays on page, no redirect
        assert resp.status_code == 200
        assert b'Passwords must match' in resp.data

    def test_set_password_strength_validation(self, client, seed_admin, seed_user):
        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/users/testuser/set-password',
            data={
                'new_password': 'weak',
                'confirm_password': 'weak',
            },
            follow_redirects=True,
        )
        assert b'Password must be at least 8 characters' in resp.data
```

---

### A.7 — Implementation checklist

- [ ] Create `app/dashboard/forms.py` with `AdminSetPasswordForm`
- [ ] Add `update_user_password` to the import block in `app/dashboard/routes.py`
- [ ] Add `from app.dashboard.forms import AdminSetPasswordForm` in `app/dashboard/routes.py`
- [ ] Add `set_user_password` route to `app/dashboard/routes.py`
- [ ] Create `app/templates/admin/set_user_password.html`
- [ ] Add "Set Password" link to the actions column in `app/templates/admin/users.html`
- [ ] Add tests to `tests/test_dashboard.py`

---

---

## Feature B: AI Integration with Amazon Bedrock

### Recommendation Summary

After evaluating all four options against the project constraints (POC-grade complexity, AWS serverless, Lambda cold-start budget, moto mock limitations), the recommended combination is:

| Priority | Feature | Model | Effort |
|---|---|---|---|
| 1 (implement first) | AI-Powered Email Explanation (post-submit) | Claude 3 Haiku | Medium |
| 2 (implement second) | AI Phishing Coach (post-quiz) | Claude 3 Haiku via Converse API | Medium |

**Options 2 (Dynamic Quiz Generation) and 3 (AI Threat Score) are deferred** — quiz generation requires careful admin UX for review/approval before storing to DynamoDB, and a raw "threat score" on top of the existing is_correct evaluation adds ambiguity without clear educational payoff.

---

### B.1 — Recommended Feature B-1: AI Email Explanation

#### What it does

After a student submits an inspector classification, the `api_submit` endpoint already returns an `explanation` field from the static `answer_key.py`. The AI version replaces or augments this with a dynamically generated, conversational explanation tailored to what the student actually submitted (right or wrong).

**Example:** If the student classifies a phishing email as Spam, the AI explains _why_ it was phishing, what signals they missed, and what to look for next time. If they got it right, the AI provides richer context on that technique category.

#### Why Claude 3 Haiku

- Cost: approximately $0.00025 per 1K input tokens, $0.00125 per 1K output tokens — virtually free per call.
- Latency: ~300–700 ms typical, well within Lambda's 30-second API Gateway timeout.
- Capability: sufficient for 100–150 word educational explanations.
- Alternative (Claude 3.5 Sonnet): 10x more expensive per token; not justified for this use case.

#### Latency strategy

The submit endpoint is already a POST that returns JSON. The AI call happens synchronously within that request. Typical latency is under 1 second for Haiku at short output lengths. No streaming or async architecture is needed for a POC. For production, a simple DynamoDB cache keyed on `(email_file, classification, selected_signals_tuple)` can eliminate repeat calls for popular combinations.

---

### B.2 — Recommended Feature B-2: Phishing Coach (post-quiz)

#### What it does

After a student finishes a quiz (`/quiz/finish`), add a new route `/quiz/<quiz_id>/coach` that lets them ask up to 5 free-text follow-up questions to an AI phishing coach. The coach has access to the student's quiz score and the quiz topic as context, but does NOT have the individual questions/answers (to avoid answer leaking). The conversation is held in the Flask session (not persisted to DynamoDB), so it is ephemeral and GDPR-clean.

#### Why Bedrock Converse API

The `bedrock-runtime:InvokeModel` API requires model-specific request body formatting. The `bedrock-runtime:Converse` API provides a unified interface that works with all Claude models and includes native multi-turn conversation support. For a chat-style interaction, Converse is the correct choice.

---

### B.3 — IAM permissions (Terraform)

Add a new IAM policy resource to `terraform/iam.tf`:

```hcl
# Bedrock access for AI features (email explanation + phishing coach)
resource "aws_iam_role_policy" "lambda_bedrock" {
  name = "${local.prefix}-lambda-bedrock"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:Converse"
        ]
        Resource = [
          # Claude 3 Haiku in eu-west-3 (Paris) — use cross-region inference if
          # the model is not available in eu-west-3; use us-east-1 ARN in that case.
          "arn:aws:bedrock:eu-west-3::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
          # Fallback: if using us-east-1 for model availability:
          # "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
        ]
      }
    ]
  })
}
```

**Important note on region:** As of 2026, Claude 3 Haiku may not be available as a foundation model in `eu-west-3` (Paris). Check the [Bedrock model availability page](https://docs.aws.amazon.com/bedrock/latest/userguide/models-regions.html). If unavailable, use `us-east-1` for the model ARN and pass `region_name='us-east-1'` when creating the Bedrock client. The Lambda's DynamoDB and S3 calls stay in `eu-west-3`; only the Bedrock call crosses regions. This adds approximately 100–200 ms of latency but is acceptable for a POC.

---

### B.4 — Lambda environment variable

Add to `terraform/lambda.tf` inside the `environment { variables = { ... } }` block:

```hcl
BEDROCK_REGION          = var.bedrock_region   # e.g. "eu-west-3" or "us-east-1"
BEDROCK_MODEL_ID        = "anthropic.claude-3-haiku-20240307-v1:0"
BEDROCK_AI_ENABLED      = "true"               # feature flag to disable at runtime
```

Add corresponding variable declarations to `terraform/variables.tf`:

```hcl
variable "bedrock_region" {
  description = "AWS region where Bedrock Claude models are available"
  type        = string
  default     = "us-east-1"
}
```

Add to `config.py`:

```python
BEDROCK_REGION   = os.environ.get('BEDROCK_REGION', 'us-east-1')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID',
                                   'anthropic.claude-3-haiku-20240307-v1:0')
BEDROCK_AI_ENABLED = os.environ.get('BEDROCK_AI_ENABLED', 'false').lower() == 'true'
```

---

### B.5 — Initialise Bedrock client in app factory

Add to `app/__init__.py` inside `create_app()`, after the S3 client block:

```python
# Initialize Bedrock runtime client (for AI features)
app.bedrock_client = boto3.client(
    'bedrock-runtime',
    region_name=app.config.get('BEDROCK_REGION', 'us-east-1'),
)
```

---

### B.6 — Model function for AI email explanation

Add to `app/models.py`:

```python
# ─── Bedrock AI helpers ───────────────────────────────────────────────────────

def generate_ai_explanation(
    email_file,
    email_subject,
    email_from,
    classification_given,
    signals_given,
    expected_classification,
    expected_signals,
    static_explanation='',
):
    """Call Bedrock Claude 3 Haiku to generate an educational explanation.

    Returns a string explanation, or the static_explanation as fallback if
    Bedrock is disabled, unavailable, or returns an error.
    """
    import json
    from flask import current_app

    if not current_app.config.get('BEDROCK_AI_ENABLED', False):
        return static_explanation

    is_correct = (
        classification_given == expected_classification
        and set(signals_given) == set(expected_signals)
    )

    if is_correct:
        outcome_context = (
            f"The student correctly identified this as {expected_classification} "
            f"and selected the right signals: {', '.join(expected_signals)}."
        )
    else:
        outcome_context = (
            f"The student classified it as '{classification_given}' "
            f"with signals [{', '.join(signals_given)}], "
            f"but the correct answer was '{expected_classification}' "
            f"with signals [{', '.join(expected_signals)}]."
        )

    prompt = (
        "You are a cybersecurity trainer teaching engineering students at ESME school "
        "how to recognise phishing and spam emails.\n\n"
        f"Email file: {email_file}\n"
        f"Subject: {email_subject}\n"
        f"Sender: {email_from}\n\n"
        f"Student outcome: {outcome_context}\n\n"
        "In 3-5 sentences, written for a non-expert student, explain:\n"
        "1. Why this email is classified as it is.\n"
        "2. What specific signals to look for in similar emails.\n"
        "3. One practical tip to avoid falling for this technique.\n\n"
        "Be encouraging, concrete, and educational. Do not repeat the classification label as a title."
    )

    try:
        client = current_app.bedrock_client
        model_id = current_app.config.get(
            'BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0'
        )
        body = json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 256,
            'messages': [{'role': 'user', 'content': prompt}],
        })
        response = client.invoke_model(
            modelId=model_id,
            body=body,
            contentType='application/json',
            accept='application/json',
        )
        result = json.loads(response['body'].read())
        return result['content'][0]['text'].strip()
    except Exception as e:
        current_app.logger.warning('Bedrock AI explanation failed: %s', e)
        return static_explanation
```

---

### B.7 — Wire AI explanation into inspector submit route

Modify the `api_submit` return in `app/inspector/routes.py`. After the `create_inspector_attempt_anonymous(...)` call and before the `return jsonify(...)`, replace the static explanation lookup:

```python
# Current code (line ~418 in routes.py):
return jsonify({
    'success': True,
    'message': 'Answer saved.',
    'completed': completed,
    'explanation': requirement.get('explanation', 'No detailed explanation available for this sample.')
})

# Proposed replacement:
from app.models import generate_ai_explanation

ai_explanation = generate_ai_explanation(
    email_file=filename,
    email_subject='',           # not available here; pass empty string
    email_from='',              # not available here; pass empty string
    classification_given=classification,
    signals_given=normalized_selected,
    expected_classification=expected_classification,
    expected_signals=normalized_expected,
    static_explanation=requirement.get('explanation', ''),
)

return jsonify({
    'success': True,
    'message': 'Answer saved.',
    'completed': completed,
    'explanation': ai_explanation,
})
```

Note: email subject/from are available in S3 but parsing them again inside `api_submit` would add an S3 read. For a POC, passing empty strings is fine since the prompt still has `email_file` as context. For a full implementation, cache the parsed summary in the session alongside `inspector_email_pool`.

---

### B.8 — Model function for Phishing Coach

Add to `app/models.py`:

```python
def call_phishing_coach(
    conversation_history,
    quiz_title,
    quiz_score,
    quiz_total,
):
    """Call Bedrock Converse API for a multi-turn phishing coach chat.

    conversation_history: list of {'role': 'user'|'assistant', 'content': str}
    Returns (assistant_reply_str, updated_history_list) or (None, history) on error.
    """
    from flask import current_app

    if not current_app.config.get('BEDROCK_AI_ENABLED', False):
        return None, conversation_history

    system_prompt = (
        "You are a friendly phishing awareness coach for engineering students at ESME school. "
        f"The student just completed the quiz '{quiz_title}' and scored {quiz_score}/{quiz_total}. "
        "Answer their questions about phishing techniques, email security, and cybersecurity awareness. "
        "Keep answers concise (3-6 sentences), practical, and encouraging. "
        "Do not answer questions unrelated to phishing or cybersecurity."
    )

    # Bedrock Converse API format
    messages = [
        {'role': msg['role'], 'content': [{'text': msg['content']}]}
        for msg in conversation_history
    ]

    try:
        client = current_app.bedrock_client
        model_id = current_app.config.get(
            'BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0'
        )
        response = client.converse(
            modelId=model_id,
            system=[{'text': system_prompt}],
            messages=messages,
            inferenceConfig={'maxTokens': 300, 'temperature': 0.7},
        )
        reply = response['output']['message']['content'][0]['text'].strip()
        updated_history = conversation_history + [
            {'role': 'assistant', 'content': reply}
        ]
        return reply, updated_history
    except Exception as e:
        current_app.logger.warning('Bedrock phishing coach failed: %s', e)
        return None, conversation_history
```

---

### B.9 — Coach route

Add to `app/quiz/routes.py`:

```python
@bp.route('/<quiz_id>/coach', methods=['GET', 'POST'])
@login_required
def phishing_coach(quiz_id):
    """Post-quiz AI phishing coach — ephemeral conversation in session."""
    quiz = get_quiz(quiz_id)
    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('quiz.quiz_list'))

    attempt = get_attempt(current_user.username, quiz_id)
    if not attempt:
        flash('Complete the quiz first to access the coach.', 'warning')
        return redirect(url_for('quiz.quiz_list'))

    from flask import current_app
    ai_enabled = current_app.config.get('BEDROCK_AI_ENABLED', False)

    session_key = f'coach_history_{quiz_id}'
    history = session.get(session_key, [])
    reply = None
    error = None

    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        max_turns = 5
        if len([m for m in history if m['role'] == 'user']) >= max_turns:
            flash('You have reached the maximum of 5 questions for this session.', 'info')
        elif question:
            history = history + [{'role': 'user', 'content': question}]
            from app.models import call_phishing_coach
            reply, history = call_phishing_coach(
                conversation_history=history,
                quiz_title=quiz['title'],
                quiz_score=int(attempt['score']),
                quiz_total=int(attempt['total']),
            )
            if reply is None:
                error = 'The AI coach is temporarily unavailable. Please try again later.'
                # Remove the unanswered user turn from history
                history = history[:-1]
            session[session_key] = history

    return render_template(
        'quiz/coach.html',
        quiz=quiz,
        attempt=attempt,
        history=history,
        ai_enabled=ai_enabled,
        error=error,
    )
```

---

### B.10 — Coach template

Create `app/templates/quiz/coach.html`:

```html
{% extends "base.html" %}
{% block title %}Phishing Coach — {{ quiz.title }}{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <nav aria-label="breadcrumb" class="mb-3">
            <ol class="breadcrumb">
                <li class="breadcrumb-item">
                    <a href="{{ url_for('quiz.quiz_list') }}">Quizzes</a>
                </li>
                <li class="breadcrumb-item active">Phishing Coach</li>
            </ol>
        </nav>

        <div class="card mb-4">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">AI Phishing Coach</h5>
                <span class="badge bg-primary">{{ quiz.title }}</span>
            </div>
            <div class="card-body">
                <p class="text-muted">
                    Your score: <strong>{{ attempt.score }}/{{ attempt.total }}</strong>
                    ({{ attempt.percentage }}%). Ask me anything about the phishing techniques
                    covered in this quiz. You have up to 5 questions.
                </p>

                {% if not ai_enabled %}
                <div class="alert alert-warning">
                    The AI coach is not enabled in this environment.
                </div>
                {% endif %}

                {% if error %}
                <div class="alert alert-danger">{{ error }}</div>
                {% endif %}

                {% if history %}
                <div class="border rounded p-3 mb-3" style="max-height: 400px; overflow-y: auto;"
                     id="chat-history">
                    {% for msg in history %}
                    <div class="mb-3 {% if msg.role == 'user' %}text-end{% endif %}">
                        <span class="badge {% if msg.role == 'user' %}bg-primary{% else %}bg-secondary{% endif %} mb-1">
                            {% if msg.role == 'user' %}You{% else %}Coach{% endif %}
                        </span>
                        <div class="p-2 rounded {% if msg.role == 'user' %}bg-primary bg-opacity-10{% else %}bg-light{% endif %}">
                            {{ msg.content }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}

                {% set questions_asked = history | selectattr('role', 'equalto', 'user') | list | length %}
                {% if questions_asked < 5 and ai_enabled %}
                <form method="POST">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <div class="mb-3">
                        <label for="question" class="form-label">
                            Your question ({{ 5 - questions_asked }} remaining)
                        </label>
                        <textarea class="form-control" id="question" name="question"
                                  rows="3" required
                                  placeholder="e.g. What makes spoofed sender addresses hard to detect?"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">Ask Coach</button>
                </form>
                {% elif questions_asked >= 5 %}
                <div class="alert alert-info">
                    You have used all 5 questions for this session.
                </div>
                {% endif %}
            </div>
        </div>

        <a href="{{ url_for('quiz.quiz_list') }}" class="btn btn-outline-secondary">
            Back to Quizzes
        </a>
    </div>
</div>
{% block scripts %}
<script>
    // Auto-scroll chat history to bottom on page load
    const chatHistory = document.getElementById('chat-history');
    if (chatHistory) {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
</script>
{% endblock %}
{% endblock %}
```

---

### B.11 — Add coach link on quiz results page

In `app/templates/quiz/results.html`, add a "Ask the Phishing Coach" button inside the existing button group:

```html
{% if not already_completed %}
<div class="mt-3">
    <a href="{{ url_for('quiz.phishing_coach', quiz_id=quiz_id) }}"
       class="btn btn-outline-info">
       Ask the AI Phishing Coach
    </a>
</div>
{% endif %}
```

---

### B.12 — Testing approach (moto does not support Bedrock)

Moto does not implement `bedrock-runtime`. The correct approach is to mock the Bedrock client with `unittest.mock.patch` at the `app.bedrock_client` level.

```python
# tests/test_bedrock.py
from unittest.mock import MagicMock, patch
import json

from tests.conftest import login


class TestAIExplanation:
    """Tests for the AI email explanation feature."""

    def _make_bedrock_response(self, text):
        """Build a mock boto3 bedrock invoke_model response."""
        body_bytes = json.dumps({
            'content': [{'text': text}]
        }).encode('utf-8')
        mock_stream = MagicMock()
        mock_stream.read.return_value = body_bytes
        return {'body': mock_stream}

    def test_explanation_returned_when_ai_enabled(self, client, app, seed_admin):
        """When BEDROCK_AI_ENABLED=True, explanation comes from Bedrock."""
        app.config['BEDROCK_AI_ENABLED'] = True

        mock_response = self._make_bedrock_response('This is an AI explanation.')

        with patch.object(app.bedrock_client, 'invoke_model',
                          return_value=mock_response) as mock_invoke:
            # (Set up inspector pool in session and submit via the inspector API)
            # ... set up session pool and S3 EML fixture per existing inspector tests ...
            # Then assert the explanation in the response equals 'This is an AI explanation.'
            pass  # Replace with full inspector fixture setup

    def test_explanation_falls_back_to_static_when_ai_disabled(self, client, app):
        """When BEDROCK_AI_ENABLED=False, static explanation is used."""
        app.config['BEDROCK_AI_ENABLED'] = False
        # Verify no bedrock_client.invoke_model call is made
        with patch.object(app.bedrock_client, 'invoke_model') as mock_invoke:
            from app.models import generate_ai_explanation
            with app.app_context():
                result = generate_ai_explanation(
                    email_file='test.eml',
                    email_subject='Test',
                    email_from='x@y.com',
                    classification_given='Phishing',
                    signals_given=['spoof'],
                    expected_classification='Phishing',
                    expected_signals=['spoof'],
                    static_explanation='Static explanation text',
                )
            assert result == 'Static explanation text'
            mock_invoke.assert_not_called()

    def test_explanation_falls_back_on_bedrock_exception(self, app):
        """When Bedrock raises an exception, static explanation is returned."""
        app.config['BEDROCK_AI_ENABLED'] = True
        with patch.object(app.bedrock_client, 'invoke_model',
                          side_effect=Exception('Bedrock unavailable')):
            from app.models import generate_ai_explanation
            with app.app_context():
                result = generate_ai_explanation(
                    email_file='test.eml',
                    email_subject='Test',
                    email_from='x@y.com',
                    classification_given='Spam',
                    signals_given=[],
                    expected_classification='Spam',
                    expected_signals=[],
                    static_explanation='Fallback explanation',
                )
            assert result == 'Fallback explanation'


class TestPhishingCoach:
    """Tests for the AI phishing coach route."""

    def _make_converse_response(self, text):
        return {
            'output': {
                'message': {
                    'content': [{'text': text}]
                }
            }
        }

    def test_coach_page_requires_completed_quiz(self, client, seed_user, seed_quiz):
        login(client, 'testuser', 'password123')
        # No attempt exists — should redirect with warning
        resp = client.get('/quiz/quiz-test/coach', follow_redirects=True)
        assert b'Complete the quiz first' in resp.data

    def test_coach_page_renders_after_quiz_completion(self, client, app,
                                                        seed_user, seed_quiz):
        with app.app_context():
            from app.models import create_attempt
            create_attempt('testuser', 'quiz-test', 2, 2)
        login(client, 'testuser', 'password123')
        resp = client.get('/quiz/quiz-test/coach')
        assert resp.status_code == 200
        assert b'Phishing Coach' in resp.data

    def test_coach_ask_question_calls_bedrock(self, client, app, seed_user, seed_quiz):
        with app.app_context():
            from app.models import create_attempt
            create_attempt('testuser', 'quiz-test', 2, 2)

        app.config['BEDROCK_AI_ENABLED'] = True
        mock_resp = self._make_converse_response('Great question! Spoofed headers work by...')

        login(client, 'testuser', 'password123')
        with patch.object(app.bedrock_client, 'converse', return_value=mock_resp):
            resp = client.post(
                '/quiz/quiz-test/coach',
                data={'question': 'How do spoofed headers work?'},
                follow_redirects=True,
            )
        assert resp.status_code == 200
        assert b'Spoofed headers work by' in resp.data

    def test_coach_limits_to_5_questions(self, client, app, seed_user, seed_quiz):
        with app.app_context():
            from app.models import create_attempt
            create_attempt('testuser', 'quiz-test', 2, 2)

        app.config['BEDROCK_AI_ENABLED'] = True
        mock_resp = self._make_converse_response('Answer.')

        login(client, 'testuser', 'password123')
        with patch.object(app.bedrock_client, 'converse', return_value=mock_resp):
            for i in range(5):
                client.post('/quiz/quiz-test/coach',
                            data={'question': f'Question {i}'})
            resp = client.post('/quiz/quiz-test/coach',
                               data={'question': 'Question 6'},
                               follow_redirects=True)
        assert b'maximum of 5 questions' in resp.data
```

**Key testing principles:**
- `BEDROCK_AI_ENABLED` is `False` in the `conftest.py` app (default `os.environ.get` returns `'false'`) so no tests accidentally call Bedrock unless they explicitly set the flag.
- Always patch `app.bedrock_client.invoke_model` / `app.bedrock_client.converse` — not the module-level import — because the client is attached to the app object.
- Test the fallback path (exception raises) for every Bedrock call to ensure graceful degradation.

---

### B.13 — Implementation checklist

- [ ] Add `BEDROCK_REGION`, `BEDROCK_MODEL_ID`, `BEDROCK_AI_ENABLED` to `config.py`
- [ ] Add `app.bedrock_client` initialisation to `app/__init__.py`
- [ ] Add `aws_iam_role_policy.lambda_bedrock` to `terraform/iam.tf`
- [ ] Add Bedrock env vars to `terraform/lambda.tf` environment block
- [ ] Add `bedrock_region` variable to `terraform/variables.tf`
- [ ] Add `generate_ai_explanation()` to `app/models.py`
- [ ] Modify `api_submit` in `app/inspector/routes.py` to call `generate_ai_explanation`
- [ ] Add `call_phishing_coach()` to `app/models.py`
- [ ] Add `phishing_coach` route to `app/quiz/routes.py`
- [ ] Create `app/templates/quiz/coach.html`
- [ ] Add coach link to `app/templates/quiz/results.html`
- [ ] Create `tests/test_bedrock.py` with mock-based tests
- [ ] Verify Bedrock model availability in `eu-west-3` or update region to `us-east-1`

---

---

## Feature C: UI/UX Improvements

### Audit Summary

After reading all templates, the static CSS (`app/static/css/style.css` is only 20 lines), and the JavaScript in `inspector.html`, the following concrete issues were identified. Each recommendation is actionable — not generic advice.

---

### C.1 — Inspector: no mobile layout for the email reading pane

**Problem:** The inspector uses a fixed two-column layout (`aside` + `section.content`) with `clamp(260px, 28%, 360px)` for the sidebar. On screens below 960 px, the media query stacks them vertically, but the aside gets `max-height: 320px` and the email details section fills the remaining viewport. On a phone, the HTML email iframe (`min-height: 520px`) causes the content panel to overflow off-screen with no visual affordance to scroll horizontally.

**Fix:** In `app/templates/inspector/inspector.html`, modify the mobile CSS:

```css
@media (max-width: 960px) {
  main {
    flex-direction: column;
    overflow: visible;   /* was: (unset — inherits hidden from main) */
  }

  aside {
    width: 100%;
    max-height: 240px;  /* slightly tighter to give email body more room */
  }

  iframe.email-html {
    min-height: 320px;  /* reduce from 520px on mobile */
    max-height: 480px;
  }

  .content {
    width: 100%;
    overflow: visible;
  }
}
```

---

### C.2 — Inspector: completion alert() is a blocking browser dialog

**Problem:** When a student completes all 8 emails, the current JavaScript calls `alert("All emails completed!...")` which is a blocking, unstyled native browser dialog. This is jarring and cannot be styled or tested easily.

**Fix:** Replace the `alert()` call in `inspector.html` with an inline Bootstrap-style modal or a styled overlay. Since the inspector does not extend `base.html`, it cannot use Bootstrap's JS bundle directly unless a script tag is added. The simplest fix that fits the existing architecture is an inline styled overlay:

```javascript
// Replace the current alert() + redirect block:
if (payload.completed) {
    showCompletionOverlay();
}

function showCompletionOverlay() {
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed; inset: 0; background: rgba(15,23,42,0.85);
        display: flex; align-items: center; justify-content: center;
        z-index: 9999; padding: 1rem;
    `;
    overlay.innerHTML = `
        <div style="background:#fff; border-radius:1rem; padding:2rem;
                    max-width:420px; text-align:center; box-shadow:0 24px 60px rgba(0,0,0,0.35);">
            <div style="font-size:2.5rem; margin-bottom:0.75rem;">&#x2705;</div>
            <h2 style="margin:0 0 0.5rem; color:#0f172a;">All done!</h2>
            <p style="color:#475569; margin:0 0 1.5rem;">
                You have reviewed all emails in this session.
                Your answers have been saved.
            </p>
            <a href="/" style="display:inline-block; background:#bef264; color:#0f172a;
                               font-weight:600; padding:0.65rem 1.75rem; border-radius:999px;
                               text-decoration:none;">
                Return to App
            </a>
        </div>
    `;
    document.body.appendChild(overlay);
}
```

---

### C.3 — Quiz: no loading state between question submissions

**Problem:** When a student clicks "Submit Answer", the form performs a full page POST. On a slow connection (Lambda cold start + API Gateway can take 2–5 seconds), there is no visual feedback — the button remains active and students may double-click, causing duplicate POST attempts. The one-attempt-per-quiz DynamoDB condition expression catches duplicate attempts, but the UX is still jarring.

**Fix:** Add a loading state to the submit button in `app/templates/quiz/take_quiz.html`:

```html
{# In take_quiz.html, replace the existing submit button rendering: #}
{{ form.submit(class="btn btn-primary", id="submit-btn") }}

{% block scripts %}
<script>
    document.querySelector('#submit-btn')?.closest('form')
        ?.addEventListener('submit', function() {
            const btn = document.querySelector('#submit-btn');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"' +
                    ' role="status" aria-hidden="true"></span>Submitting...';
            }
        });
</script>
{% endblock %}
```

---

### C.4 — Dashboard: users table has no search or filter

**Problem:** The `/dashboard/users` page loads ALL users in a single `list_all_users()` call and renders them in one unsearchable table. With 100+ students this becomes very slow to scan visually.

**Fix:** Add a client-side filter using an `<input>` and a few lines of JS. No backend changes needed:

```html
{# Add above the table in admin/users.html: #}
<div class="mb-3">
    <input type="text" id="user-search" class="form-control"
           placeholder="Filter by username, email, class, facility..."
           aria-label="Filter users">
</div>

{% block scripts %}
<script>
    document.getElementById('user-search').addEventListener('input', function() {
        const query = this.value.toLowerCase();
        document.querySelectorAll('tbody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
        });
    });
</script>
{% endblock %}
```

---

### C.5 — Base template: navbar active state is not indicated

**Problem:** The navbar in `base.html` has no `active` class applied to the current page's nav item. Users have no visual indication of where they are in the app, which is a basic accessibility and orientation issue (WCAG 2.4.4 — Link Purpose).

**Fix:** In `base.html`, use `request.endpoint` to add `active` to the correct nav item:

```html
{# Replace static nav-link anchors with conditional active class: #}
<li class="nav-item">
    <a class="nav-link {% if request.endpoint and request.endpoint.startswith('quiz.') %}active{% endif %}"
       href="{{ url_for('quiz.quiz_list') }}">Quizzes</a>
</li>
<li class="nav-item">
    <a class="nav-link {% if request.endpoint == 'quiz.history' %}active{% endif %}"
       href="{{ url_for('quiz.history') }}">My History</a>
</li>
<li class="nav-item">
    <a class="nav-link {% if request.endpoint and request.endpoint.startswith('inspector.') %}active{% endif %}"
       href="{{ url_for('inspector.index') }}">Email Inspector</a>
</li>
```

---

### C.6 — Inspector: no progress counter for students

**Problem:** Students have no visible indication of how many emails they have reviewed vs. how many remain. The only cue is the submit response says "completed: true" when done, which triggers the alert. Without progress visibility, students don't know if they submitted 3 or 7 of their 8 emails.

**Fix:** The `/inspector/api/emails` response already returns the pool. After loading the email list, render a progress counter in the sidebar header. This is a pure frontend change in `inspector.html`:

```javascript
// In renderEmailList(), after setting emailListContainer content,
// update the list-header with a count:
function renderEmailList(emails) {
    // ... existing logic ...
    const listHeader = document.querySelector('.list-header');
    if (listHeader) {
        listHeader.textContent = `Available Emails (${emails.length})`;
    }
}
```

For submitted-email tracking, the JS `classificationLog` array already records every submission. Use it:

```javascript
// After a successful submit in the form submit handler:
const submittedCount = classificationLog.length;
const totalEmails = emailListContainer.querySelectorAll('.email-item').length;
const listHeader = document.querySelector('.list-header');
if (listHeader) {
    listHeader.textContent = `Emails — ${submittedCount}/${totalEmails} done`;
}
// Also visually mark the submitted email in the list:
const emailButton = emailListContainer.querySelector(`[data-file-name="${escapeHtml(emailFileName)}"]`);
if (emailButton) {
    emailButton.style.opacity = '0.5';
    emailButton.querySelector('.subject').textContent += ' (Submitted)';
}
```

---

### C.7 — Video gate: no visual indicator that the video has been watched

**Problem:** The video gate at `/quiz/<quiz_id>/video` requires students to watch the video before starting the quiz. The "Start Quiz" button is shown after a JavaScript `video_watched` POST, but there is no visual cue that the system registered the watch event — students sometimes click the button before the response returns and see nothing happen.

The current `video_gate.html` template was not read in detail, but based on the route logic in `quiz/routes.py`, the pattern is a JS POST to `/quiz/<quiz_id>/video-watched` that unlocks a button. The fix is to show a brief loading spinner on the button while the POST is in flight, then reveal it with a success message.

**Effort:** Small

---

### C.8 — Forms: password fields have no show/hide toggle

**Problem:** Both `auth/change_password.html` and the proposed `admin/set_user_password.html` use plain `<input type="password">` fields with no reveal toggle. This increases mis-entry errors, especially on mobile.

**Fix:** Add a reusable Jinja2 macro or a small vanilla-JS snippet that wraps password inputs with an eye-icon toggle:

```html
{# Add to base.html's {% block scripts %} or as a standalone <script> in the form template: #}
<script>
document.querySelectorAll('input[type="password"]').forEach(function(input) {
    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.innerHTML = '&#128065;';
    btn.title = 'Show/hide password';
    btn.style.cssText = 'position:absolute;right:0.6rem;top:50%;transform:translateY(-50%);' +
        'background:none;border:none;cursor:pointer;font-size:1.1rem;padding:0;color:#6c757d;';
    btn.addEventListener('click', function() {
        input.type = input.type === 'password' ? 'text' : 'password';
    });
    wrapper.appendChild(btn);
});
</script>
```

This can be added to `base.html`'s `{% block scripts %}` default block so it applies site-wide.

---

### C.9 — Accessibility: inspector iframe has no title for screen readers

**Problem:** In `inspector.html`, the HTML preview iframe is rendered without a `title` attribute:

```javascript
`<iframe class="email-html" sandbox="allow-same-origin"></iframe>`
```

WCAG 2.4.1 requires frames to have titles. The fix is to add `title="HTML email preview"` to the iframe element in the JS string that builds it.

---

### C.10 — Quiz results: no "review wrong answers" capability

**Problem:** The results page shows only the final score. Students who score poorly have no way to see which questions they answered incorrectly. The `get_responses(username, quiz_id)` function in `app/models.py` already retrieves per-question responses, but the results route does not use it.

**Recommended enhancement to the results route in `app/quiz/routes.py`:**

```python
# In finish_quiz(), before render_template:
from app.models import get_responses
responses = get_responses(current_user.username, quiz_id) if quiz_id else []

# Build a lookup for the template: question_id -> {is_correct, selected_answer_id}
response_map = {r['question_id']: r for r in responses}

return render_template(
    'quiz/results.html',
    score=score,
    total=total,
    quiz_id=quiz_id,
    video_url=video_url,
    quiz=quiz,               # pass quiz so template has question text
    response_map=response_map,
)
```

Then in `quiz/results.html`, add an expandable "Review Answers" section that shows each question, the student's answer, and whether it was correct. This is the highest-value UX improvement in this list — it directly supports the educational purpose of the app.

---

### C.11 — Summary table

| # | Issue | Affected file(s) | Effort | Priority |
|---|---|---|---|---|
| C.1 | Inspector mobile iframe overflow | `inspector/inspector.html` | Small | High |
| C.2 | Replace blocking alert() | `inspector/inspector.html` | Small | High |
| C.3 | Quiz submit button loading state | `quiz/take_quiz.html` | Small | Medium |
| C.4 | User table search filter | `admin/users.html` | Small | Medium |
| C.5 | Navbar active state | `base.html` | Small | Low |
| C.6 | Inspector progress counter | `inspector/inspector.html` | Small | Medium |
| C.7 | Video gate watch confirmation | `quiz/video_gate.html` | Small | Low |
| C.8 | Password show/hide toggle | `base.html` + password forms | Small | Low |
| C.9 | iframe title for a11y | `inspector/inspector.html` | Trivial | Low |
| C.10 | Review wrong answers on results | `quiz/routes.py` + `quiz/results.html` | Medium | High |

---

---

## Implementation Order and Dependencies

### Recommended order

```
Phase 1 — No dependencies, immediate value (1–3 days total)
  1. Feature A (Admin password change) — Small, zero risk, fills obvious gap
  2. Feature C.1 + C.2 + C.3 (Inspector mobile, alert, quiz spinner) — frontend-only, no backend

Phase 2 — UI completeness (1–2 days)
  3. Feature C.4 + C.5 + C.6 (users table search, nav active, inspector progress)
  4. Feature C.10 (review wrong answers) — requires small route change + template

Phase 3 — AI integration (3–5 days including testing)
  5. Feature B.1 — Email explanation AI (after Terraform apply to add Bedrock IAM)
  6. Feature B.2 — Phishing Coach (depends on B.1 infrastructure being in place)
```

### Dependency map

```
Feature A       →  no dependencies
Feature C.1–9   →  no dependencies (frontend/template only, except C.10)
Feature C.10    →  requires get_responses() (already exists in models.py)
Feature B.1     →  requires: IAM Terraform change, BEDROCK_AI_ENABLED config key,
                            app.bedrock_client in __init__.py
Feature B.2     →  requires: same Bedrock infrastructure as B.1
                   (can be developed in parallel after infrastructure is in place)
```

### Risk notes

- **Feature A** carries minimal risk. The `update_user_password` model function is already battle-tested via the student change-password flow. The only new surface is the admin route, which is guarded by the same `is_admin` check used by all other dashboard routes.
- **Feature B** carries latency risk. If Bedrock is unavailable (cold service, region issue, IAM misconfiguration), both functions degrade gracefully to the static explanation/None. The feature flag `BEDROCK_AI_ENABLED=false` is the kill switch. Test the fallback path before deploying the happy path.
- **Feature B — region caveat**: If `anthropic.claude-3-haiku-20240307-v1:0` is not available in `eu-west-3`, you must either request model access through the AWS console or point the Bedrock client at `us-east-1`. Verify model availability before the Terraform apply.
- **Feature C** items are all low-risk since they are frontend-only. The only one with backend surface is C.10 (review wrong answers), which adds one `get_responses()` call to an existing route.
