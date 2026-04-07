"""Tests for M3 threat feed feature (OpenPhish integration).

Covers:
 - GET  /dashboard/api/threat-feed          — fetch & defang URLs from OpenPhish (mocked)
 - POST /dashboard/api/threat-feed/promote  — promote a threat URL into the inspector dataset
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import login


class TestThreatFeed:
    """GET /dashboard/api/threat-feed"""

    def test_threat_feed_requires_admin(self, client, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.get('/dashboard/api/threat-feed')
        assert resp.status_code == 403

    def test_threat_feed_returns_list(self, client, seed_admin):
        """When the external request fails the endpoint should return an empty list."""
        login(client, 'admin', 'admin123')
        with patch('app.dashboard.routes.requests.get') as mock_get:
            mock_get.side_effect = Exception('network error')
            resp = client.get('/dashboard/api/threat-feed')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)

    def test_threat_feed_defangs_urls(self, client, seed_admin):
        """URLs returned by the feed are defanged (hxxp, [.] notation)."""
        import app.dashboard.routes as dashboard_routes
        dashboard_routes.THREAT_CACHE['data'] = []
        dashboard_routes.THREAT_CACHE['timestamp'] = 0

        login(client, 'admin', 'admin123')
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = (
            "http://paypal.evil.com/login\n"
            "http://microsoft.phish.net/verify\n"
            "https://google.fake.org/account\n"
        )
        with patch('app.dashboard.routes.requests.get', return_value=mock_response):
            resp = client.get('/dashboard/api/threat-feed')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data) > 0
        for entry in data:
            assert 'url' in entry
            # Defanged URLs must not contain 'http://' or 'https://'
            assert 'http://' not in entry['url']
            assert 'https://' not in entry['url']
            assert 'hxxp' in entry['url']

    def test_threat_feed_identifies_known_targets(self, client, seed_admin):
        """Heuristic target detection for common brands."""
        import app.dashboard.routes as dashboard_routes
        dashboard_routes.THREAT_CACHE['data'] = []
        dashboard_routes.THREAT_CACHE['timestamp'] = 0

        login(client, 'admin', 'admin123')
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = (
            "http://paypal.evil.com/scam\n"
            "http://microsoft.login.fake.com/auth\n"
            "http://amazon.badsite.com/prime\n"
            "http://apple.icloud-secure.com/verify\n"
        )
        with patch('app.dashboard.routes.requests.get', return_value=mock_response):
            resp = client.get('/dashboard/api/threat-feed')
        data = json.loads(resp.data)
        targets = {entry['target'] for entry in data}
        assert 'PayPal' in targets
        assert 'Microsoft' in targets
        assert 'Amazon' in targets
        assert 'Apple' in targets

    def test_threat_feed_uses_cache(self, client, seed_admin, app):
        """Second call returns cached data without hitting the network again."""
        import app.dashboard.routes as dashboard_routes

        # Reset the in-process cache so this test starts clean
        dashboard_routes.THREAT_CACHE['data'] = []
        dashboard_routes.THREAT_CACHE['timestamp'] = 0

        login(client, 'admin', 'admin123')
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "http://cached-phish.com/page\n"
        with patch('app.dashboard.routes.requests.get', return_value=mock_response) as mock_get:
            client.get('/dashboard/api/threat-feed')
            client.get('/dashboard/api/threat-feed')
            # The network should only have been called once (second call uses cache)
            assert mock_get.call_count == 1


class TestPromoteThreatToInspector:
    """POST /dashboard/api/threat-feed/promote"""

    def test_promote_requires_admin(self, client, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.post(
            '/dashboard/api/threat-feed/promote',
            json={'raw_url': 'http://evil.com/login', 'target': 'Unknown'},
        )
        assert resp.status_code == 403

    def test_promote_missing_url_returns_400(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/api/threat-feed/promote',
            json={'target': 'PayPal'},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'url is required' in data['error']

    def test_promote_saves_to_s3_and_answer_key(self, client, seed_admin, app):
        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/api/threat-feed/promote',
            json={
                'raw_url': 'http://evil-phish.com/fake-login',
                'target': 'Google',
                'filename': 'test-promoted.json',
            },
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True
        assert data['email_file'] == 'test-promoted.json'

        # Verify the file was stored in S3
        with app.app_context():
            bucket = app.config['S3_BUCKET']
            obj = app.s3_client.get_object(Bucket=bucket, Key='eml-samples/test-promoted.json')
            body = json.loads(obj['Body'].read().decode('utf-8'))
            assert 'evil-phish.com' in body['textBody']
            assert body['summary']['fileName'] == 'test-promoted.json'

        # Verify answer key override was set
        from app.models import get_effective_answer_key
        with app.app_context():
            ak = get_effective_answer_key()
        assert 'test-promoted.json' in ak
        assert ak['test-promoted.json']['classification'] == 'Phishing'
        assert 'externaldomain' in ak['test-promoted.json']['signals']

    def test_promote_auto_generates_filename(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/api/threat-feed/promote',
            json={'raw_url': 'http://evil.net/page', 'target': 'Unknown'},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['email_file'].endswith('.json')

    def test_promote_appends_json_extension(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/api/threat-feed/promote',
            json={
                'raw_url': 'http://phish.net/x',
                'target': 'Unknown',
                'filename': 'no-extension',
            },
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['email_file'].endswith('.json')
