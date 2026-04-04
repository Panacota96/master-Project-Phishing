"""Tests for answer key override CRUD and effective merge logic (app/models.py)."""
import pytest

from tests.conftest import login


class TestAnswerKeyOverrides:
    """set_answer_key_override / delete_answer_key_override / get_effective_answer_key."""

    # ── helpers ──────────────────────────────────────────────────────────────

    def _put_override(self, app, filename, classification, signals, explanation='test'):
        with app.app_context():
            from app.models import set_answer_key_override
            set_answer_key_override(filename, classification, signals, explanation)

    # ── get_answer_key_overrides ─────────────────────────────────────────────

    def test_overrides_empty_initially(self, app):
        with app.app_context():
            from app.models import get_answer_key_overrides
            assert get_answer_key_overrides() == {}

    # ── set_answer_key_override ──────────────────────────────────────────────

    def test_set_override_stores_entry(self, app):
        with app.app_context():
            from app.models import get_answer_key_overrides, set_answer_key_override
            set_answer_key_override(
                'test-email.eml', 'Phishing', ['impersonation', 'urgency'], 'Test explanation'
            )
            overrides = get_answer_key_overrides()
            assert 'test-email.eml' in overrides
            entry = overrides['test-email.eml']
            assert entry['classification'] == 'Phishing'
            assert 'impersonation' in entry['signals']
            assert 'urgency' in entry['signals']

    def test_set_override_normalizes_signals(self, app):
        """Signals are lowercased and deduplicated on write."""
        with app.app_context():
            from app.models import get_answer_key_overrides, set_answer_key_override
            set_answer_key_override('norm.eml', 'Spam', ['Impersonation', 'URGENCY', 'urgency'])
            overrides = get_answer_key_overrides()
            signals = overrides['norm.eml']['signals']
            assert signals == ['impersonation', 'urgency']

    def test_set_override_invalid_classification_raises(self, app):
        with app.app_context():
            from app.models import set_answer_key_override
            with pytest.raises(ValueError, match='classification'):
                set_answer_key_override('bad.eml', 'Malware', ['urgency'])

    def test_set_override_invalid_signal_raises(self, app):
        with app.app_context():
            from app.models import set_answer_key_override
            with pytest.raises(ValueError, match='signal'):
                set_answer_key_override('bad.eml', 'Phishing', ['not-a-signal'])

    def test_set_override_spam_with_no_signals(self, app):
        """Spam entries legitimately have zero signals."""
        with app.app_context():
            from app.models import get_answer_key_overrides, set_answer_key_override
            set_answer_key_override('spam.eml', 'Spam', [])
            overrides = get_answer_key_overrides()
            assert overrides['spam.eml']['signals'] == []

    # ── delete_answer_key_override ───────────────────────────────────────────

    def test_delete_override_removes_entry(self, app):
        with app.app_context():
            from app.models import (
                delete_answer_key_override,
                get_answer_key_overrides,
                set_answer_key_override,
            )
            set_answer_key_override('del.eml', 'Phishing', ['urgency'])
            assert 'del.eml' in get_answer_key_overrides()
            delete_answer_key_override('del.eml')
            assert 'del.eml' not in get_answer_key_overrides()

    def test_delete_nonexistent_override_is_idempotent(self, app):
        """Deleting a non-existent override must not raise."""
        with app.app_context():
            from app.models import delete_answer_key_override
            delete_answer_key_override('ghost.eml')  # should not raise

    # ── get_effective_answer_key ─────────────────────────────────────────────

    def test_effective_key_includes_static_entries(self, app):
        with app.app_context():
            from app.inspector.answer_key import ANSWER_KEY
            from app.models import get_effective_answer_key
            effective = get_effective_answer_key()
            for filename in ANSWER_KEY:
                assert filename in effective

    def test_override_takes_precedence_over_static(self, app):
        """An override must replace the static answer key entry."""
        with app.app_context():
            from app.inspector.answer_key import ANSWER_KEY
            from app.models import get_effective_answer_key, set_answer_key_override

            # Pick any Phishing entry from the static key and override it as Spam
            phishing_file = next(
                k for k, v in ANSWER_KEY.items() if v['classification'] == 'Phishing'
            )
            set_answer_key_override(phishing_file, 'Spam', [])
            effective = get_effective_answer_key()
            assert effective[phishing_file]['classification'] == 'Spam'
            assert effective[phishing_file]['signals'] == []

    def test_delete_override_reverts_to_static(self, app):
        """Deleting an override should expose the original static entry again."""
        with app.app_context():
            from app.inspector.answer_key import ANSWER_KEY
            from app.models import (
                delete_answer_key_override,
                get_effective_answer_key,
                set_answer_key_override,
            )
            phishing_file = next(
                k for k, v in ANSWER_KEY.items() if v['classification'] == 'Phishing'
            )
            original_signals = ANSWER_KEY[phishing_file]['signals']

            set_answer_key_override(phishing_file, 'Spam', [])
            delete_answer_key_override(phishing_file)

            effective = get_effective_answer_key()
            assert effective[phishing_file]['classification'] == 'Phishing'
            assert sorted(effective[phishing_file]['signals']) == sorted(original_signals)

    def test_effective_key_signals_are_normalized(self, app):
        """Signals from the effective answer key are always lowercase strings."""
        with app.app_context():
            from app.models import get_effective_answer_key
            effective = get_effective_answer_key()
            for filename, entry in effective.items():
                for signal in entry['signals']:
                    assert signal == signal.lower(), (
                        f"{filename}: signal '{signal}' is not lowercase"
                    )

    def test_override_for_new_email_file(self, app):
        """An override for a file not in the static key is also surfaced."""
        with app.app_context():
            from app.models import get_effective_answer_key, set_answer_key_override
            set_answer_key_override(
                'brand-new.eml', 'Phishing', ['impersonation', 'spoof'], 'New entry'
            )
            effective = get_effective_answer_key()
            assert 'brand-new.eml' in effective
            assert effective['brand-new.eml']['explanation'] == 'New entry'

    # ── admin route integration ───────────────────────────────────────────────

    def test_admin_answer_key_edit_route(self, client, seed_admin):
        """Admin can update an override via the HTTP route."""
        from app.inspector.answer_key import ANSWER_KEY
        login(client, 'admin', 'admin123')

        phishing_file = next(
            k for k, v in ANSWER_KEY.items() if v['classification'] == 'Phishing'
        )
        resp = client.post(
            '/dashboard/inspector/answer-key/edit',
            data={
                'email_file': phishing_file,
                'classification': 'Spam',
                'signals': '',
                'explanation': 'Admin override test',
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_admin_answer_key_reset_route(self, client, seed_admin, app):
        """Admin can reset (delete) an override via the HTTP route."""
        from app.inspector.answer_key import ANSWER_KEY
        with app.app_context():
            from app.models import set_answer_key_override
            phishing_file = next(
                k for k, v in ANSWER_KEY.items() if v['classification'] == 'Phishing'
            )
            set_answer_key_override(phishing_file, 'Spam', [])

        login(client, 'admin', 'admin123')
        resp = client.post(
            '/dashboard/inspector/answer-key/reset',
            data={'email_file': phishing_file},
            follow_redirects=True,
        )
        assert resp.status_code == 200
