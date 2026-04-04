"""Tests for inspector routes and anonymous submissions."""

from app.inspector.answer_key import ANSWER_KEY
from conftest import login


def _seed_eml_files(app, filenames):
    with app.app_context():
        for name in filenames:
            body = f"Subject: Test {name}\n\nHello".encode("utf-8")
            app.s3_client.put_object(
                Bucket=app.config['S3_BUCKET'],
                Key=f"eml-samples/{name}",
                Body=body,
            )


class TestInspectorEmails:
    def test_email_pool_stable_within_session(self, client, app, seed_user):
        filenames = list(ANSWER_KEY.keys())[:10]
        _seed_eml_files(app, filenames)
        login(client, 'testuser', 'password123')

        resp1 = client.get('/inspector/api/emails')
        assert resp1.status_code == 200
        data1 = resp1.get_json()
        emails1 = [e['fileName'] for e in data1.get('emails', [])]
        assert 0 < len(emails1) <= 8

        resp2 = client.get('/inspector/api/emails')
        assert resp2.status_code == 200
        data2 = resp2.get_json()
        emails2 = [e['fileName'] for e in data2.get('emails', [])]

        assert emails1 == emails2

    def test_email_pool_spam_bounds(self, client, app, seed_user):
        spam_files = [k for k, v in ANSWER_KEY.items() if v['classification'] == 'Spam']
        phishing_files = [k for k, v in ANSWER_KEY.items() if v['classification'] == 'Phishing']
        filenames = spam_files[:5] + phishing_files[:10]
        _seed_eml_files(app, filenames)
        login(client, 'testuser', 'password123')

        resp = client.get('/inspector/api/emails')
        assert resp.status_code == 200
        data = resp.get_json()
        emails = [e['fileName'] for e in data.get('emails', [])]
        assert len(emails) == 8
        spam_count = sum(1 for name in emails if ANSWER_KEY[name]['classification'] == 'Spam')
        assert 1 <= spam_count <= 3


class TestInspectorSubmit:
    def test_submit_saves_anonymous_attempt(self, client, app, seed_user):
        filename, requirement = next(iter(ANSWER_KEY.items()))
        _seed_eml_files(app, [filename])
        login(client, 'testuser', 'password123')
        client.get('/inspector/api/emails')

        resp = client.post('/inspector/api/submit', json={
            'fileName': filename,
            'classification': requirement['classification'],
            'signals': requirement['signals'],
        })
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload.get('message') == 'Answer saved.'

        with app.app_context():
            table = app.dynamodb.Table(app.config['DYNAMODB_INSPECTOR_ANON'])
            items = table.scan().get('Items', [])
            assert items
            saved = items[-1]
            assert saved.get('email_file') == filename
            assert saved.get('is_correct') is True
            assert 'username' not in saved

    def test_submit_incorrect_with_wrong_signal(self, client, app, seed_user):
        filename, requirement = next(iter(ANSWER_KEY.items()))
        if requirement['classification'] != 'Phishing':
            filename, requirement = next(
                (k, v) for k, v in ANSWER_KEY.items() if v['classification'] == 'Phishing'
            )

        _seed_eml_files(app, [filename])
        login(client, 'testuser', 'password123')
        client.get('/inspector/api/emails')

        wrong_signals = requirement['signals'][:2] + ['not-a-signal']
        resp = client.post('/inspector/api/submit', json={
            'fileName': filename,
            'classification': 'Phishing',
            'signals': wrong_signals,
        })
        assert resp.status_code == 200

        with app.app_context():
            table = app.dynamodb.Table(app.config['DYNAMODB_INSPECTOR_ANON'])
            items = table.scan().get('Items', [])
            assert items
            saved = items[-1]
            assert saved.get('email_file') == filename
            assert saved.get('is_correct') is False


class TestInspectorValidation:
    """Edge-case tests for inspector submission validation logic."""

    def test_spam_correct_with_no_signals(self, client, app, seed_user):
        """A Spam email requires zero signals; submitting none must be correct."""
        spam_file = next(k for k, v in ANSWER_KEY.items() if v['classification'] == 'Spam')
        _seed_eml_files(app, [spam_file])
        login(client, 'testuser', 'password123')
        client.get('/inspector/api/emails')

        resp = client.post('/inspector/api/submit', json={
            'fileName': spam_file,
            'classification': 'Spam',
            'signals': [],
        })
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload.get('message') == 'Answer saved.'

        with app.app_context():
            table = app.dynamodb.Table(app.config['DYNAMODB_INSPECTOR_ANON'])
            items = table.scan().get('Items', [])
            saved = next(i for i in items if i.get('email_file') == spam_file)
            assert saved['is_correct'] is True

    def test_spam_incorrect_when_classified_as_phishing(self, client, app, seed_user):
        """Classifying a Spam email as Phishing must be marked incorrect."""
        spam_file = next(k for k, v in ANSWER_KEY.items() if v['classification'] == 'Spam')
        _seed_eml_files(app, [spam_file])
        login(client, 'testuser', 'password123')
        client.get('/inspector/api/emails')

        # Spam entries have 0 expected signals, so Phishing with 0 signals passes
        # input validation but the classification mismatch makes it incorrect.
        resp = client.post('/inspector/api/submit', json={
            'fileName': spam_file,
            'classification': 'Phishing',
            'signals': [],
        })
        assert resp.status_code == 200

        with app.app_context():
            table = app.dynamodb.Table(app.config['DYNAMODB_INSPECTOR_ANON'])
            items = table.scan().get('Items', [])
            saved = next(i for i in items if i.get('email_file') == spam_file)
            assert saved['is_correct'] is False

    def test_override_changes_correctness_verdict(self, client, app, seed_user):
        """When an admin overrides a Phishing email to Spam the student
        must be marked correct when they submit Spam with no signals."""
        phishing_file, _ = next(
            (k, v) for k, v in ANSWER_KEY.items() if v['classification'] == 'Phishing'
        )
        _seed_eml_files(app, [phishing_file])

        # Admin overrides the entry to Spam
        with app.app_context():
            from app.models import set_answer_key_override
            set_answer_key_override(phishing_file, 'Spam', [])

        login(client, 'testuser', 'password123')
        client.get('/inspector/api/emails')

        resp = client.post('/inspector/api/submit', json={
            'fileName': phishing_file,
            'classification': 'Spam',
            'signals': [],
        })
        assert resp.status_code == 200

        with app.app_context():
            table = app.dynamodb.Table(app.config['DYNAMODB_INSPECTOR_ANON'])
            items = table.scan().get('Items', [])
            saved = next(i for i in items if i.get('email_file') == phishing_file)
            assert saved['is_correct'] is True

    def test_unknown_file_rejected(self, client, app, seed_user):
        """Submitting a fileName not in the session pool must not return HTTP 500."""
        login(client, 'testuser', 'password123')
        client.get('/inspector/api/emails')

        resp = client.post('/inspector/api/submit', json={
            'fileName': 'totally-unknown-file.eml',
            'classification': 'Phishing',
            'signals': ['urgency'],
        })
        # The route should handle this gracefully (4xx or a JSON error, not 500)
        assert resp.status_code in (400, 403, 404, 200)
        if resp.status_code == 200:
            payload = resp.get_json()
            assert payload is not None
