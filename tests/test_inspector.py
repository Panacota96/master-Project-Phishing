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
