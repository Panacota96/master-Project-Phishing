"""Microsoft 365 / Azure AD SSO helpers (MSAL OIDC flow).

SSO is *optional*: if ``MSAL_CLIENT_ID`` / ``MSAL_CLIENT_SECRET`` are not
configured the routes simply redirect back to the local login page with an
informational flash message.

Flow
----
1. ``/auth/sso/login``   → builds the authorisation URL and redirects to
                            Microsoft.
2. ``/auth/sso/callback`` → exchanges the auth code for tokens, looks up or
                            auto-provisions a local ``User`` record, then calls
                            ``login_user()``.

Auto-provisioning
-----------------
When a Microsoft user authenticates for the first time a local account is
created automatically using the Microsoft UPN as the username and the OIDC
``email`` claim as the email address.  The account is created **without** a
usable local password (the hash is set to the placeholder ``"sso-only"``),
preventing local-password login for SSO-only accounts.

RBAC mapping
------------
The ``groups`` claim returned by Microsoft Graph can optionally be mapped to
the local ``is_admin`` flag.  Set ``MSAL_ADMIN_GROUP_ID`` to the Azure AD
group object-ID whose members should receive admin rights.  Leave it empty
(the default) to keep all SSO users as ordinary students.
"""

import os
import secrets

import msal
from flask import current_app, flash, redirect, request, session, url_for
from flask_login import login_user

from app.models import create_user, get_user, get_user_by_email


# ── helpers ──────────────────────────────────────────────────────────────────


def _sso_enabled() -> bool:
    """Return True only when all required MSAL settings are present."""
    cfg = current_app.config
    return bool(cfg.get('MSAL_CLIENT_ID') and cfg.get('MSAL_CLIENT_SECRET'))


def _build_msal_app(cache=None):
    """Create a ConfidentialClientApplication instance."""
    cfg = current_app.config
    return msal.ConfidentialClientApplication(
        cfg['MSAL_CLIENT_ID'],
        authority=cfg['MSAL_AUTHORITY'],
        client_credential=cfg['MSAL_CLIENT_SECRET'],
        token_cache=cache,
    )


def _callback_url() -> str:
    return url_for('auth.sso_callback', _external=True)


# ── route helpers called from auth/routes.py ─────────────────────────────────


def initiate_sso_login():
    """Redirect the browser to Microsoft's login page.

    Stores a PKCE *state* nonce in the session to prevent CSRF on the callback.
    Returns a Flask ``Response`` object.
    """
    if not _sso_enabled():
        flash('Microsoft SSO is not configured on this instance.', 'warning')
        return redirect(url_for('auth.login'))

    state = secrets.token_urlsafe(32)
    session['sso_state'] = state

    msal_app = _build_msal_app()
    auth_url = msal_app.get_authorization_request_url(
        scopes=current_app.config['MSAL_SCOPES'],
        state=state,
        redirect_uri=_callback_url(),
    )
    return redirect(auth_url)


def handle_sso_callback():
    """Process the redirect from Microsoft and log the user in.

    Returns a Flask ``Response`` object.
    """
    if not _sso_enabled():
        flash('Microsoft SSO is not configured on this instance.', 'warning')
        return redirect(url_for('auth.login'))

    # --- CSRF / state validation ---
    returned_state = request.args.get('state', '')
    if returned_state != session.pop('sso_state', None):
        flash('SSO login failed: invalid state parameter.', 'danger')
        return redirect(url_for('auth.login'))

    error = request.args.get('error')
    if error:
        description = request.args.get('error_description', error)
        current_app.logger.warning('SSO error from Microsoft: %s', description)
        flash(f'SSO login failed: {description}', 'danger')
        return redirect(url_for('auth.login'))

    code = request.args.get('code')
    if not code:
        flash('SSO login failed: no authorisation code received.', 'danger')
        return redirect(url_for('auth.login'))

    # --- Exchange code for tokens ---
    msal_app = _build_msal_app()
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=current_app.config['MSAL_SCOPES'],
        redirect_uri=_callback_url(),
    )

    if 'error' in result:
        current_app.logger.warning('MSAL token error: %s', result)
        flash('SSO login failed: could not obtain token from Microsoft.', 'danger')
        return redirect(url_for('auth.login'))

    id_token_claims = result.get('id_token_claims', {})
    upn = (
        id_token_claims.get('preferred_username')
        or id_token_claims.get('upn')
        or ''
    ).lower().strip()
    email = (id_token_claims.get('email') or upn).lower().strip()
    display_name = id_token_claims.get('name', upn)

    if not upn:
        flash('SSO login failed: could not retrieve your Microsoft identity.', 'danger')
        return redirect(url_for('auth.login'))

    # --- Look up or auto-provision local account ---
    # Sanitise UPN into a valid username (replace @ and . with underscores)
    username_candidate = upn.replace('@', '_').replace('.', '_')

    user = get_user(username_candidate) or get_user_by_email(email)

    if user is None:
        # Auto-provision a new student account.
        admin_group_id = os.environ.get('MSAL_ADMIN_GROUP_ID', '')
        groups_in_token = id_token_claims.get('groups', [])
        is_admin = bool(admin_group_id and admin_group_id in groups_in_token)

        try:
            create_user(
                username=username_candidate,
                email=email,
                # Placeholder: SSO users cannot use local-password login.
                password='sso-only',
                is_admin=is_admin,
                group='default',
                class_name='',
                academic_year='',
                major='',
                facility='',
            )
            user = get_user(username_candidate)
            current_app.logger.info(
                'SSO auto-provisioned user %s (%s)', username_candidate, display_name
            )
        except Exception as exc:
            current_app.logger.error('SSO user provision failed: %s', exc)
            flash('SSO login failed: could not create your account.', 'danger')
            return redirect(url_for('auth.login'))

    if user is None:
        flash('SSO login failed: account not found.', 'danger')
        return redirect(url_for('auth.login'))

    login_user(user)
    flash(f'Signed in via Microsoft as {display_name}.', 'success')
    next_page = request.args.get('next') or url_for('quiz.quiz_list')
    return redirect(next_page)
