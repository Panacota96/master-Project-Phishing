"""Tests for M2/M3 campaign functionality.

Covers:
 - GET  /dashboard/api/campaigns   — list campaigns
 - POST /dashboard/campaigns/launch — launch a campaign (queues to SQS)
 - POST /dashboard/campaigns/validation-email — send validation emails via SES
"""
import json

from app.models import create_user, list_campaigns
from tests.conftest import login


class TestListCampaigns:
    """GET /dashboard/api/campaigns"""

    def test_list_campaigns_requires_admin(self, client, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.get('/dashboard/api/campaigns')
        assert resp.status_code == 403

    def test_list_campaigns_empty(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.get('/dashboard/api/campaigns')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'campaigns' in data
        assert isinstance(data['campaigns'], list)

    def test_list_campaigns_returns_created_campaigns(self, client, seed_admin, app):
        from app.models import create_campaign
        with app.app_context():
            create_campaign('ClassA|2025|CS|ESME|All', {
                'class_name': 'ClassA',
                'academic_year': '2025',
                'major': 'CS',
                'facility': 'ESME',
                'group': 'All',
            })

        login(client, 'admin', 'admin123')
        resp = client.get('/dashboard/api/campaigns')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        campaigns = data['campaigns']
        assert len(campaigns) >= 1
        assert campaigns[0]['cohort'] == 'ClassA|2025|CS|ESME|All'


class TestLaunchCampaign:
    """POST /dashboard/campaigns/launch"""

    def test_launch_campaign_requires_admin(self, client, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.post('/dashboard/campaigns/launch', data={
            'class_name': 'ClassA',
            'academic_year': '2025',
            'major': 'CS',
        })
        assert resp.status_code == 403

    def test_launch_campaign_creates_campaign_and_queues(self, client, seed_admin, app):
        login(client, 'admin', 'admin123')
        resp = client.post('/dashboard/campaigns/launch', data={
            'class_name': 'ClassA',
            'academic_year': '2025',
            'major': 'CS',
            'facility': 'ESME',
            'group': 'g1',
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True
        assert 'campaign' in data
        campaign = data['campaign']
        assert campaign['cohort'] == 'ClassA|2025|CS|ESME|g1'
        assert campaign['status'] == 'queued'

    def test_launch_campaign_persists_to_dynamo(self, client, seed_admin, app):
        login(client, 'admin', 'admin123')
        resp = client.post('/dashboard/campaigns/launch', data={
            'class_name': 'ClassB',
            'academic_year': '2026',
            'major': 'IT',
            'facility': 'ESME',
            'group': 'All',
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        campaign_id = data['campaign']['campaign_id']

        with app.app_context():
            campaigns = list_campaigns()
        ids = [c['campaign_id'] for c in campaigns]
        assert campaign_id in ids

    def test_launch_campaign_all_filters_default(self, client, seed_admin):
        """Launching without filters should still succeed (targets all users)."""
        login(client, 'admin', 'admin123')
        resp = client.post('/dashboard/campaigns/launch', data={})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True
        # Cohort string should represent "All" for every field
        assert 'All' in data['campaign']['cohort']

    def test_launch_campaign_cohort_string_shorthand(self, client, seed_admin):
        """cohort POST field is parsed into individual filter keys."""
        login(client, 'admin', 'admin123')
        resp = client.post('/dashboard/campaigns/launch', data={
            'cohort': 'ClassC|2025|Sec|Lyon|grp1',
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'ClassC' in data['campaign']['cohort']


class TestValidationEmail:
    """POST /dashboard/campaigns/validation-email"""

    def test_validation_email_requires_admin(self, client, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.post('/dashboard/campaigns/validation-email', data={
            'class_name': 'ClassA',
            'academic_year': '2025',
            'major': 'CS',
        })
        assert resp.status_code == 403

    def test_validation_email_no_matching_users_returns_404(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.post('/dashboard/campaigns/validation-email', data={
            'class_name': 'NonExistent',
            'academic_year': '9999',
            'major': 'Alien',
        })
        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert 'No matching users' in data['error']

    def test_validation_email_sends_to_matching_users(self, client, seed_admin, app):
        with app.app_context():
            create_user(
                'val_student',
                'val@test.com',
                'TestPass1!',
                group='g1',
                class_name='ValidClass',
                academic_year='2025',
                major='CS',
            )
            # Verify the sender identity in the SES mock so sending is allowed
            import boto3
            ses = boto3.client('ses', region_name='eu-west-3')
            ses.verify_email_identity(EmailAddress='no-reply@test.example.com')

        login(client, 'admin', 'admin123')
        resp = client.post('/dashboard/campaigns/validation-email', data={
            'class_name': 'ValidClass',
            'academic_year': '2025',
            'major': 'CS',
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True
        assert 'sent 1' in data['message']

    def test_validation_email_no_ses_configured_returns_400(self, client, seed_admin, app, monkeypatch):
        monkeypatch.setenv('SES_FROM_EMAIL', '')
        # Recreate client with the new env var cleared
        with app.app_context():
            app.config['SES_FROM_EMAIL'] = ''
        login(client, 'admin', 'admin123')
        resp = client.post('/dashboard/campaigns/validation-email', data={
            'class_name': 'Any',
        })
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'SES_FROM_EMAIL' in data['error']
