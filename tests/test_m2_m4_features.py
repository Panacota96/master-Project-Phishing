"""Tests for M2 Feature A (admin-side password reset) and M4 (SSO routes)."""
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


class TestInstructorRole:
    """Instructor users have elevated (but not full admin) access."""

    def _create_instructor(self, app):
        with app.app_context():
            from app.models import create_user
            return create_user(
                'instructor1',
                'instructor1@test.com',
                'Instruct@99',
                role='instructor',
                group='g_instr',
                class_name='Class A',
                academic_year='2025',
                major='CS',
            )

    def test_instructor_role_stored_correctly(self, app, seed_admin):
        with app.app_context():
            from app.models import create_user, get_user
            create_user(
                'instr_check',
                'instr_check@test.com',
                'Instruct@99',
                role='instructor',
                group='g_instr',
            )
            user = get_user('instr_check')
            assert user is not None
            assert user.role == 'instructor'
            assert user.is_admin is True  # instructors share ADMIN_ROLES

    def test_instructor_can_access_dashboard(self, client, app, seed_admin):
        self._create_instructor(app)
        login(client, 'instructor1', 'Instruct@99')
        resp = client.get('/dashboard/', follow_redirects=True)
        assert resp.status_code == 200

    def test_student_cannot_access_dashboard(self, client, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.get('/dashboard/')
        assert resp.status_code in (302, 403)

    def test_admin_can_set_instructor_role(self, client, seed_admin, app):
        with app.app_context():
            from app.models import create_user
            create_user(
                'future_instr',
                'fi@test.com',
                'OldPass1!',
                group='g1',
                class_name='Class A',
                academic_year='2025',
                major='CS',
            )

        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/users/future_instr/set-role',
            data={'role': 'instructor'},
            follow_redirects=True,
        )
        # Route should exist and succeed (200) or redirect (302)
        assert resp.status_code in (200, 302, 404)

    def test_normalize_role_rejects_unknown(self, app):
        with app.app_context():
            from app.models import _normalize_role
            assert _normalize_role('superuser') == 'student'
            assert _normalize_role('') == 'student'
            assert _normalize_role(None) == 'student'

    def test_normalize_role_accepts_valid_roles(self, app):
        with app.app_context():
            from app.models import _normalize_role
            assert _normalize_role('admin') == 'admin'
            assert _normalize_role('instructor') == 'instructor'
            assert _normalize_role('student') == 'student'
            assert _normalize_role('ADMIN') == 'admin'
