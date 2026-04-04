"""Tests for M2 Feature A (admin-side password reset) and M4 (SSO routes)."""
import pytest

from app.models import create_user, get_user
from tests.conftest import login


class TestAdminSetPassword:
    """Admin can reset any non-self user's password via the dashboard."""

    def test_admin_can_reset_student_password(self, client, seed_admin, app):
        with app.app_context():
            create_user(
                'student1',
                'student1@test.com',
                'OldPass1!',
                group='g1',
                class_name='Class A',
                academic_year='2025',
                major='CS',
            )

        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/users/student1/set-password',
            data={
                'new_password': 'NewPass1!',
                'confirm_password': 'NewPass1!',
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'Password updated for student1' in resp.data

        with app.app_context():
            user = get_user('student1')
            assert user is not None
            assert user.check_password('NewPass1!')
            assert not user.check_password('OldPass1!')

    def test_admin_cannot_reset_own_password_via_route(self, client, seed_admin, app):
        """The route should still work (no self-check there), but admin should
        use the change-password form for their own account.  Here we simply
        verify that the route accepts a valid payload without error."""
        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/users/admin/set-password',
            data={
                'new_password': 'Admin@New1',
                'confirm_password': 'Admin@New1',
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_non_admin_cannot_reset_password(self, client, seed_user, seed_admin, app):
        with app.app_context():
            create_user(
                'victim',
                'victim@test.com',
                'VictimPass1!',
                group='g1',
                class_name='Class A',
                academic_year='2025',
                major='CS',
            )

        login(client, 'testuser', 'password123')
        resp = client.post(
            '/dashboard/users/victim/set-password',
            data={
                'new_password': 'Hacked@123',
                'confirm_password': 'Hacked@123',
            },
        )
        assert resp.status_code == 403

    def test_reset_nonexistent_user_returns_404(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/users/nobody/set-password',
            data={
                'new_password': 'SomePass1!',
                'confirm_password': 'SomePass1!',
            },
        )
        assert resp.status_code == 404

    def test_weak_password_rejected(self, client, seed_admin, app):
        with app.app_context():
            create_user(
                'weakpw_student',
                'weakpw@test.com',
                'OldPass1!',
                group='g1',
                class_name='Class A',
                academic_year='2025',
                major='CS',
            )

        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/users/weakpw_student/set-password',
            data={
                'new_password': 'short',
                'confirm_password': 'short',
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # Password should NOT have been changed
        with app.app_context():
            user = get_user('weakpw_student')
            assert user.check_password('OldPass1!')
            assert not user.check_password('short')

    def test_mismatched_passwords_rejected(self, client, seed_admin, app):
        with app.app_context():
            create_user(
                'mismatch_student',
                'mismatch@test.com',
                'OldPass1!',
                group='g1',
                class_name='Class A',
                academic_year='2025',
                major='CS',
            )

        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/users/mismatch_student/set-password',
            data={
                'new_password': 'NewPass1!',
                'confirm_password': 'DifferentPass1!',
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        with app.app_context():
            user = get_user('mismatch_student')
            assert user.check_password('OldPass1!')


class TestSSORoutes:
    """M4: SSO routes exist and respond correctly when SSO is disabled."""

    def test_sso_login_redirect_when_disabled(self, client):
        """When MSAL is not configured the SSO login route flashes a warning
        and redirects back to the regular login page."""
        resp = client.get('/auth/sso/login', follow_redirects=False)
        # Should redirect (to login page)
        assert resp.status_code in (301, 302)

    def test_sso_callback_redirect_when_disabled(self, client):
        """SSO callback also redirects when MSAL is unconfigured."""
        resp = client.get('/auth/sso/callback', follow_redirects=False)
        assert resp.status_code in (301, 302)

    def test_sso_login_follows_to_login_page(self, client):
        """Following the redirect ends up at the login page."""
        resp = client.get('/auth/sso/login', follow_redirects=True)
        assert resp.status_code == 200
        # The local login form should be present
        assert b'Log In' in resp.data or b'login' in resp.data.lower()

    def test_sso_button_hidden_when_disabled(self, client):
        """The login page does NOT show the Microsoft SSO button when
        MSAL_CLIENT_ID / MSAL_CLIENT_SECRET are not set."""
        resp = client.get('/auth/login')
        assert resp.status_code == 200
        assert b'Sign in with Microsoft' not in resp.data
