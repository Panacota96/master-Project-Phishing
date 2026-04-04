"""Tests for per-cohort inspector configuration (app/models.py)."""


class TestInspectorConfig:
    """get_inspector_config_for_cohort / save_inspector_config_for_cohort."""

    _COHORT = dict(
        class_name='Class A',
        academic_year='2025',
        major='CS',
        facility='Paris',
        group='engineering',
    )

    def test_defaults_returned_when_no_config(self, app):
        """With no persisted config the function must return the global defaults."""
        with app.app_context():
            from app.models import get_inspector_config_for_cohort
            cfg = get_inspector_config_for_cohort(**self._COHORT)
            assert 'pool_size' in cfg
            assert 'max_spam' in cfg
            assert 'spam_ratio' in cfg
            assert 'targets' in cfg
            assert isinstance(cfg['pool_size'], int)
            assert isinstance(cfg['spam_ratio'], float)

    def test_defaults_match_config_constants(self, app):
        with app.app_context():
            from app.models import get_inspector_config_for_cohort
            cfg = get_inspector_config_for_cohort(**self._COHORT)
            assert cfg['pool_size'] == app.config.get('INSPECTOR_POOL_SIZE_DEFAULT', 8)
            assert cfg['max_spam'] == app.config.get('INSPECTOR_MAX_SPAM_DEFAULT', 3)

    def test_save_and_retrieve_config(self, app):
        """Persisting a config via DynamoDB must be retrievable in the same context."""
        with app.app_context():
            from app.models import (
                get_inspector_config_for_cohort,
                save_inspector_config_for_cohort,
            )
            custom = {
                'pool_size': 5,
                'max_spam': 1,
                'spam_ratio': 0.2,
                'targets': [],
            }
            save_inspector_config_for_cohort(**self._COHORT, config=custom)
            # Clear the in-memory cache so we hit DynamoDB
            app.extensions.pop('inspector_cohort_config', None)
            retrieved = get_inspector_config_for_cohort(**self._COHORT)
            assert int(retrieved['pool_size']) == 5
            assert int(retrieved['max_spam']) == 1

    def test_different_cohorts_have_independent_configs(self, app):
        """Two distinct cohorts must not share configuration."""
        cohort_a = dict(
            class_name='Class A', academic_year='2025', major='CS',
            facility='Paris', group='eng',
        )
        cohort_b = dict(
            class_name='Class B', academic_year='2026', major='Math',
            facility='Lyon', group='sci',
        )
        with app.app_context():
            from app.models import (
                get_inspector_config_for_cohort,
                save_inspector_config_for_cohort,
            )
            custom_a = {'pool_size': 4, 'max_spam': 0, 'spam_ratio': 0.0, 'targets': []}
            save_inspector_config_for_cohort(**cohort_a, config=custom_a)

            app.extensions.pop('inspector_cohort_config', None)
            cfg_b = get_inspector_config_for_cohort(**cohort_b)
            # Cohort B should NOT see Cohort A's pool_size of 4
            assert int(cfg_b['pool_size']) != 4

    def test_save_config_with_target_list(self, app):
        """A whitelist of target filenames is stored and retrieved."""
        with app.app_context():
            from app.models import (
                get_inspector_config_for_cohort,
                save_inspector_config_for_cohort,
            )
            targets = ['phishing-a.eml', 'phishing-b.eml', 'spam-c.eml']
            save_inspector_config_for_cohort(
                **self._COHORT,
                config={'pool_size': 3, 'max_spam': 1, 'spam_ratio': 0.33, 'targets': targets},
            )
            app.extensions.pop('inspector_cohort_config', None)
            cfg = get_inspector_config_for_cohort(**self._COHORT)
            assert list(cfg.get('targets', [])) == targets

    def test_memory_cache_avoids_extra_dynamo_call(self, app):
        """Second call to get_inspector_config_for_cohort should hit the in-memory cache."""
        with app.app_context():
            from app.models import (
                get_inspector_config_for_cohort,
                save_inspector_config_for_cohort,
            )
            save_inspector_config_for_cohort(
                **self._COHORT,
                config={'pool_size': 7, 'max_spam': 2, 'spam_ratio': 0.28, 'targets': []},
            )
            cfg1 = get_inspector_config_for_cohort(**self._COHORT)
            cfg2 = get_inspector_config_for_cohort(**self._COHORT)
            # Both calls must return the same object (from cache)
            assert int(cfg1['pool_size']) == int(cfg2['pool_size'])
