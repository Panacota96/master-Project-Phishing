"""Tests for Microsoft 365 / Azure AD SSO authentication flow.

Coverage
--------
* SSO disabled — routes redirect gracefully when MSAL is not configured.
* SSO login initiation (``initiate_sso_login``):
  - Redirects browser to the Microsoft authorisation URL.
  - Stores a PKCE state nonce in the session.
  - Persists a safe *next* path in the session.
  - Rejects external / open-redirect *next* values.
* SSO callback (``handle_sso_callback``):
  - Rejects mismatching or missing state parameters (CSRF protection).
  - Handles error responses from Microsoft.
  - Handles missing authorisation code.
  - Handles MSAL token-exchange failures.
  - Handles tokens that carry no UPN / preferred_username.
  - Auto-provisions a new *student* account on first login.
  - Auto-provisions *admin* role for users in the configured admin group.
  - Auto-provisions *instructor* role for users in the instructor group.
  - Updates an existing user's role when group membership changes.
  - Finds an existing account by e-mail address when the username differs.
  - Redirects to the ``sso_next`` path stored by the login step.
* Login page UI:
  - "Sign in with Microsoft" button present when SSO is enabled.
  - Button absent when SSO credentials are not configured.
"""

from unittest.mock import MagicMock, patch

import pytest  # noqa: F401 — used implicitly by fixtures


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _enable_sso(app, admin_group='', instructor_group=''):
    """Inject fake MSAL credentials into the running test app config."""
    app.config['MSAL_CLIENT_ID'] = 'fake-client-id'
    app.config['MSAL_CLIENT_SECRET'] = 'fake-client-secret'
    app.config['MSAL_AUTHORITY'] = 'https://login.microsoftonline.com/common/v2.0'
    app.config['MSAL_SCOPES'] = ['openid', 'profile', 'email', 'User.Read', 'GroupMember.Read.All']
    app.config['MSAL_ADMIN_GROUP_ID'] = admin_group
    app.config['MSAL_INSTRUCTOR_GROUP_ID'] = instructor_group


def _mock_msal_app(
    auth_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize?state=test',
    token_result=None,
):
    """Return a ``MagicMock`` that stands in for a MSAL ConfidentialClientApplication."""
    mock = MagicMock()
    mock.get_authorization_request_url.return_value = auth_url
    if token_result is None:
        token_result = _default_token_result('alice@esme.fr', 'Alice Dupont', [])
    mock.acquire_token_by_authorization_code.return_value = token_result
    return mock


def _default_token_result(upn, name='Test User', groups=None):
    """Build a minimal MSAL token result dict."""
    return {
        'id_token_claims': {
            'preferred_username': upn,
            'email': upn,
            'name': name,
            'groups': groups or [],
        }
    }


# ---------------------------------------------------------------------------
# SSO disabled — MSAL credentials not configured
# ---------------------------------------------------------------------------

class TestSSODisabled:
    """Routes behave gracefully when SSO is not configured."""

    def test_sso_login_redirects_with_warning_when_disabled(self, client):
        """GET /auth/sso/login → login page + warning flash when SSO is off."""
        resp = client.get('/auth/sso/login', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Microsoft SSO is not configured' in resp.data

    def test_sso_callback_redirects_with_warning_when_disabled(self, client):
        """GET /auth/sso/callback → login page + warning flash when SSO is off."""
        resp = client.get('/auth/sso/callback', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Microsoft SSO is not configured' in resp.data


# ---------------------------------------------------------------------------
# SSO login initiation
# ---------------------------------------------------------------------------

class TestSSOLogin:
    """Tests for ``initiate_sso_login()``."""

    def test_redirects_to_microsoft_auth_url(self, client, app):
        """A 302 to the Microsoft authorisation URL is returned."""
        _enable_sso(app)
        expected_url = 'https://login.microsoftonline.com/authorize?state=x'
        mock_msal = _mock_msal_app(auth_url=expected_url)
        with patch('app.auth.sso.msal.ConfidentialClientApplication', return_value=mock_msal):
            resp = client.get('/auth/sso/login')
        assert resp.status_code == 302
        assert resp.headers['Location'] == expected_url

    def test_state_nonce_stored_in_session(self, client, app):
        """A PKCE state nonce is stored in the session to prevent CSRF."""
        _enable_sso(app)
        with patch('app.auth.sso.msal.ConfidentialClientApplication', return_value=_mock_msal_app()):
            client.get('/auth/sso/login')
        with client.session_transaction() as sess:
            assert 'sso_state' in sess

    def test_valid_next_path_stored_in_session(self, client, app):
        """A safe relative *next* path is persisted in the session."""
        _enable_sso(app)
        with patch('app.auth.sso.msal.ConfidentialClientApplication', return_value=_mock_msal_app()):
            client.get('/auth/sso/login?next=/quiz/list')
        with client.session_transaction() as sess:
            assert sess.get('sso_next') == '/quiz/list'

    def test_external_next_path_rejected(self, client, app):
        """A *next* value starting with ``//`` is not stored (open-redirect guard)."""
        _enable_sso(app)
        with patch('app.auth.sso.msal.ConfidentialClientApplication', return_value=_mock_msal_app()):
            client.get('/auth/sso/login?next=//evil.example.com/phish')
        with client.session_transaction() as sess:
            assert 'sso_next' not in sess

    def test_http_absolute_next_path_rejected(self, client, app):
        """A *next* value with a scheme (``http://``) is not stored."""
        _enable_sso(app)
        with patch('app.auth.sso.msal.ConfidentialClientApplication', return_value=_mock_msal_app()):
            client.get('/auth/sso/login?next=http://evil.example.com/')
        with client.session_transaction() as sess:
            assert 'sso_next' not in sess


# ---------------------------------------------------------------------------
# SSO callback — error paths
# ---------------------------------------------------------------------------

class TestSSOCallbackErrors:
    """Error-handling tests for ``handle_sso_callback()``."""

    # ── CSRF / state validation ───────────────────────────────────────────

    def test_mismatching_state_rejected(self, client, app):
        """A state that does not match the session value triggers a danger flash."""
        _enable_sso(app)
        with client.session_transaction() as sess:
            sess['sso_state'] = 'correct-state'
        resp = client.get(
            '/auth/sso/callback?state=wrong-state&code=abc123',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'invalid state parameter' in resp.data

    def test_missing_session_state_rejected(self, client, app):
        """If no state was stored in the session the callback rejects the request."""
        _enable_sso(app)
        # No session state set — simulates a direct / replayed request.
        resp = client.get(
            '/auth/sso/callback?state=whatever&code=abc123',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'invalid state parameter' in resp.data

    # ── Microsoft-side errors ─────────────────────────────────────────────

    def test_microsoft_error_param_handled(self, client, app):
        """An ``error=`` query param from Microsoft produces a user-friendly flash."""
        _enable_sso(app)
        with client.session_transaction() as sess:
            sess['sso_state'] = 'test-state'
        resp = client.get(
            '/auth/sso/callback?state=test-state'
            '&error=access_denied&error_description=User+cancelled+login',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'SSO login failed' in resp.data

    def test_missing_authorisation_code(self, client, app):
        """No ``code=`` parameter → danger flash about missing auth code."""
        _enable_sso(app)
        with client.session_transaction() as sess:
            sess['sso_state'] = 'test-state'
        resp = client.get(
            '/auth/sso/callback?state=test-state',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'no authorisation code received' in resp.data

    # ── Token exchange failures ───────────────────────────────────────────

    def test_msal_token_exchange_failure(self, client, app):
        """MSAL returning an error dict → danger flash about token failure."""
        _enable_sso(app)
        with client.session_transaction() as sess:
            sess['sso_state'] = 'test-state'
        error_result = {'error': 'invalid_grant', 'error_description': 'Token expired'}
        mock_msal = _mock_msal_app(token_result=error_result)
        with patch('app.auth.sso.msal.ConfidentialClientApplication', return_value=mock_msal):
            resp = client.get(
                '/auth/sso/callback?state=test-state&code=abc',
                follow_redirects=True,
            )
        assert resp.status_code == 200
        assert b'could not obtain token' in resp.data

    def test_missing_upn_in_token_claims(self, client, app):
        """Token with no ``preferred_username`` / ``upn`` → danger flash."""
        _enable_sso(app)
        with client.session_transaction() as sess:
            sess['sso_state'] = 'test-state'
        empty_claims = {'id_token_claims': {'name': 'Unknown', 'groups': []}}
        mock_msal = _mock_msal_app(token_result=empty_claims)
        with patch('app.auth.sso.msal.ConfidentialClientApplication', return_value=mock_msal):
            resp = client.get(
                '/auth/sso/callback?state=test-state&code=abc',
                follow_redirects=True,
            )
        assert resp.status_code == 200
        assert b'could not retrieve your Microsoft identity' in resp.data


# ---------------------------------------------------------------------------
# SSO callback — successful flows
# ---------------------------------------------------------------------------

class TestSSOCallbackSuccess:
    """Happy-path and role-mapping tests for ``handle_sso_callback()``."""

    def _valid_callback(self, client, app, token_result, state='test-state'):
        """Helper: set session state and perform the callback request."""
        with client.session_transaction() as sess:
            sess['sso_state'] = state
        mock_msal = _mock_msal_app(token_result=token_result)
        with patch('app.auth.sso.msal.ConfidentialClientApplication', return_value=mock_msal):
            return client.get(
                f'/auth/sso/callback?state={state}&code=auth-code-xyz',
                follow_redirects=True,
            )

    # ── Auto-provisioning ─────────────────────────────────────────────────

    def test_autoprovisions_new_student(self, client, app):
        """First-time SSO login creates a new account with role=student."""
        _enable_sso(app)
        resp = self._valid_callback(
            client, app,
            _default_token_result('bob@esme.fr', 'Bob Martin'),
        )
        assert resp.status_code == 200
        assert b'Signed in via Microsoft' in resp.data
        with app.app_context():
            from app.models import get_user
            user = get_user('bob_esme_fr')
            assert user is not None
            assert user.role == 'student'
            assert user.email == 'bob@esme.fr'

    def test_autoprovisions_admin_role_for_admin_group(self, client, app):
        """SSO user in the configured admin Azure AD group gets role=admin."""
        _enable_sso(app, admin_group='admin-group-guid')
        resp = self._valid_callback(
            client, app,
            _default_token_result('charlie@esme.fr', 'Charlie Admin', ['admin-group-guid']),
        )
        assert resp.status_code == 200
        with app.app_context():
            from app.models import get_user
            user = get_user('charlie_esme_fr')
            assert user is not None
            assert user.role == 'admin'

    def test_autoprovisions_instructor_role_for_instructor_group(self, client, app):
        """SSO user in the instructor Azure AD group gets role=instructor."""
        _enable_sso(app, instructor_group='instructor-group-guid')
        resp = self._valid_callback(
            client, app,
            _default_token_result('diana@esme.fr', 'Diana Instructor', ['instructor-group-guid']),
        )
        assert resp.status_code == 200
        with app.app_context():
            from app.models import get_user
            user = get_user('diana_esme_fr')
            assert user is not None
            assert user.role == 'instructor'

    def test_admin_group_takes_priority_over_instructor_group(self, client, app):
        """When a user is in both groups, admin role wins."""
        _enable_sso(app, admin_group='admin-guid', instructor_group='instructor-guid')
        resp = self._valid_callback(
            client, app,
            _default_token_result(
                'eve@esme.fr', 'Eve Both', ['admin-guid', 'instructor-guid']
            ),
        )
        assert resp.status_code == 200
        with app.app_context():
            from app.models import get_user
            user = get_user('eve_esme_fr')
            assert user is not None
            assert user.role == 'admin'

    # ── Existing user ─────────────────────────────────────────────────────

    def test_updates_role_for_existing_user(self, client, app, seed_user):
        """An existing student's role is promoted when their Azure AD group changes."""
        _enable_sso(app, admin_group='admin-group-guid')
        # seed_user: username='testuser', email='test@test.com', role=student
        resp = self._valid_callback(
            client, app,
            _default_token_result('testuser', 'Test User', ['admin-group-guid']),
        )
        assert resp.status_code == 200
        assert b'Signed in via Microsoft' in resp.data
        with app.app_context():
            from app.models import get_user
            assert get_user('testuser').role == 'admin'

    def test_role_unchanged_when_group_membership_unchanged(self, client, app, seed_user):
        """Existing student role stays student when not in any mapped group."""
        _enable_sso(app, admin_group='admin-group-guid')
        resp = self._valid_callback(
            client, app,
            _default_token_result('testuser', 'Test User', []),
        )
        assert resp.status_code == 200
        with app.app_context():
            from app.models import get_user
            assert get_user('testuser').role == 'student'

    def test_finds_existing_user_by_email(self, client, app, seed_user):
        """Account is matched by e-mail when the UPN-derived username differs."""
        _enable_sso(app)
        # seed_user: username='testuser', email='test@test.com'
        # UPN 'different@esme.fr' → candidate username 'different_esme_fr' (no match)
        # but email 'test@test.com' will match the existing record.
        resp = self._valid_callback(
            client, app,
            {
                'id_token_claims': {
                    'preferred_username': 'different@esme.fr',
                    'email': 'test@test.com',
                    'name': 'Test User SSO',
                    'groups': [],
                }
            },
        )
        assert resp.status_code == 200
        assert b'Signed in via Microsoft' in resp.data

    # ── Post-login redirect ───────────────────────────────────────────────

    def test_redirects_to_sso_next_page(self, client, app):
        """After login the user is sent to the path stored in ``sso_next``."""
        _enable_sso(app)
        with client.session_transaction() as sess:
            sess['sso_state'] = 'test-state'
            sess['sso_next'] = '/quiz/list'
        mock_msal = _mock_msal_app(token_result=_default_token_result('frank@esme.fr'))
        with patch('app.auth.sso.msal.ConfidentialClientApplication', return_value=mock_msal):
            resp = client.get('/auth/sso/callback?state=test-state&code=abc')
        assert resp.status_code == 302
        assert '/quiz/list' in resp.headers['Location']

    def test_redirects_to_quiz_list_when_no_next(self, client, app):
        """Without a stored ``sso_next`` the redirect falls back to the quiz list."""
        _enable_sso(app)
        with client.session_transaction() as sess:
            sess['sso_state'] = 'test-state'
        mock_msal = _mock_msal_app(token_result=_default_token_result('grace@esme.fr'))
        with patch('app.auth.sso.msal.ConfidentialClientApplication', return_value=mock_msal):
            resp = client.get('/auth/sso/callback?state=test-state&code=abc')
        assert resp.status_code == 302
        assert '/quiz' in resp.headers['Location']

    def test_success_flash_includes_display_name(self, client, app):
        """The flash message after SSO login contains the user's display name."""
        _enable_sso(app)
        resp = self._valid_callback(
            client, app,
            _default_token_result('henry@esme.fr', 'Henry Leblanc'),
        )
        assert b'Henry Leblanc' in resp.data


# ---------------------------------------------------------------------------
# Login page — SSO button visibility
# ---------------------------------------------------------------------------

class TestLoginPageSSO:
    """The 'Sign in with Microsoft' button is shown/hidden based on configuration."""

    def test_sso_button_visible_when_enabled(self, client, app):
        """``Sign in with Microsoft`` link present when MSAL credentials are set."""
        _enable_sso(app)
        resp = client.get('/auth/login')
        assert resp.status_code == 200
        assert b'Sign in with Microsoft' in resp.data
        assert b'sso/login' in resp.data

    def test_sso_button_absent_when_disabled(self, client):
        """No SSO link rendered when MSAL credentials are absent."""
        resp = client.get('/auth/login')
        assert resp.status_code == 200
        assert b'sso/login' not in resp.data
        assert b'Sign in with Microsoft' not in resp.data
