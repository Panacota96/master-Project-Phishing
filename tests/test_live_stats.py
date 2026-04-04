"""Tests for M2 live stats and SSE dashboard stream.

Covers:
 - GET /dashboard/api/stats         — point-in-time stats snapshot
 - GET /dashboard/api/stats/stream  — SSE stream (initial data frame)
"""
import json

import pytest

from app.models import create_user
from tests.conftest import login


class TestLiveStats:
    """GET /dashboard/api/stats"""

    def test_stats_requires_admin(self, client, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.get('/dashboard/api/stats')
        assert resp.status_code == 403

    def test_stats_returns_expected_keys(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.get('/dashboard/api/stats')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        for key in ('total_users', 'completed_count', 'pending_count', 'avg_score'):
            assert key in data, f"Expected key '{key}' in stats response"

    def test_stats_total_users_matches_created(self, client, seed_admin, app):
        with app.app_context():
            create_user(
                's1', 's1@test.com', 'Pass1!abc',
                group='g1', class_name='A', academic_year='2025', major='CS',
            )
            create_user(
                's2', 's2@test.com', 'Pass1!abc',
                group='g1', class_name='A', academic_year='2025', major='CS',
            )

        login(client, 'admin', 'admin123')
        resp = client.get('/dashboard/api/stats')
        data = json.loads(resp.data)
        # seed_admin creates 1 admin + we added 2 students
        assert data['total_users'] >= 3

    def test_stats_no_attempts_gives_zero_avg(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.get('/dashboard/api/stats')
        data = json.loads(resp.data)
        assert data['avg_score'] == 0
        assert data['completed_count'] == 0

    def test_stats_per_group_is_dict(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.get('/dashboard/api/stats')
        data = json.loads(resp.data)
        assert 'per_group' in data
        # per_group is a dict keyed by cohort string (empty when no attempts)
        assert isinstance(data['per_group'], dict)

    def test_stats_inspector_progress_present(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.get('/dashboard/api/stats')
        data = json.loads(resp.data)
        assert 'inspector_progress' in data
        assert isinstance(data['inspector_progress'], list)


class TestStatsStream:
    """GET /dashboard/api/stats/stream — SSE endpoint."""

    def test_stream_requires_admin(self, client, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.get('/dashboard/api/stats/stream')
        assert resp.status_code == 403

    def test_stream_content_type_is_event_stream(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        # Only inspect the headers — do NOT consume the body (it's an infinite
        # SSE generator when Redis is unavailable in the test environment).
        resp = client.get('/dashboard/api/stats/stream')
        assert resp.status_code == 200
        assert 'text/event-stream' in resp.content_type

    def test_build_live_stats_returns_expected_keys(self, app, seed_admin):
        """_build_live_stats (the payload source for the SSE stream) returns
        the expected schema.  Tested directly to avoid consuming an infinite
        SSE generator in the test environment."""
        with app.app_context():
            from app.dashboard.routes import _build_live_stats
            stats = _build_live_stats()
        for key in ('total_users', 'completed_count', 'pending_count', 'avg_score',
                    'per_group', 'inspector_progress'):
            assert key in stats, f"Expected key '{key}' in live stats payload"
