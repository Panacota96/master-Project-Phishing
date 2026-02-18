import json

from app.models import (
    create_user,
    get_user_inspector_state,
    update_user_inspector_state,
)
from tests.conftest import login


class TestInspectorBulkReset:
    def test_bulk_reset_filtered_users(self, client, seed_admin, app):
        with app.app_context():
            create_user(
                'u1',
                'u1@test.com',
                'pass12345',
                group='g1',
                class_name='Class A',
                academic_year='2025',
                major='CS',
            )
            create_user(
                'u2',
                'u2@test.com',
                'pass12345',
                group='g1',
                class_name='Class B',
                academic_year='2025',
                major='CS',
            )
            create_user(
                'u3',
                'u3@test.com',
                'pass12345',
                group='g1',
                class_name='Class A',
                academic_year='2026',
                major='CS',
            )
            update_user_inspector_state('u1', submitted=['a.eml'], locked=True)
            update_user_inspector_state('u2', submitted=['b.eml'], locked=True)
            update_user_inspector_state('u3', submitted=['c.eml'], locked=True)

        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/inspector/reset-bulk',
            data={
                'scope': 'filtered',
                'class_name': 'Class A',
                'academic_year': '2025',
                'major': 'CS',
            },
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['count'] == 1

        with app.app_context():
            u1_state = get_user_inspector_state('u1')
            u2_state = get_user_inspector_state('u2')
            u3_state = get_user_inspector_state('u3')
            assert u1_state['locked'] is False
            assert u1_state['submitted'] == []
            assert u2_state['locked'] is True
            assert u3_state['locked'] is True

    def test_bulk_reset_all_excludes_admin(self, client, seed_admin, app):
        with app.app_context():
            create_user(
                'u4',
                'u4@test.com',
                'pass12345',
                group='g1',
                class_name='Class A',
                academic_year='2025',
                major='CS',
            )
            create_user(
                'u5',
                'u5@test.com',
                'pass12345',
                group='g1',
                class_name='Class A',
                academic_year='2025',
                major='CS',
            )
            update_user_inspector_state('u4', submitted=['a.eml'], locked=True)
            update_user_inspector_state('u5', submitted=['b.eml'], locked=True)
            update_user_inspector_state('admin', submitted=['admin.eml'], locked=True)

        login(client, 'admin', 'admin123')
        resp = client.post('/dashboard/inspector/reset-bulk', data={'scope': 'all'})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['count'] == 2

        with app.app_context():
            u4_state = get_user_inspector_state('u4')
            u5_state = get_user_inspector_state('u5')
            admin_state = get_user_inspector_state('admin')
            assert u4_state['locked'] is False
            assert u5_state['locked'] is False
            assert admin_state['locked'] is True

    def test_bulk_reset_requires_admin(self, client, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.post('/dashboard/inspector/reset-bulk', data={'scope': 'all'})
        assert resp.status_code == 403

    def test_bulk_reset_invalid_scope(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.post('/dashboard/inspector/reset-bulk', data={'scope': 'bad'})
        assert resp.status_code == 400
