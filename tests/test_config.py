import importlib
import sys
import types

import pytest


def _load_config_module(
    monkeypatch,
    *,
    env=None,
    secret_payload=None,
    secret_error_message=None,
):
    env = env or {}
    calls = []

    for key in (
        "SECRET_ARN",
        "SECRET_KEY",
        "MSAL_CLIENT_SECRET",
        "AWS_REGION_NAME",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    class DummyBotoCoreError(Exception):
        pass

    class DummyClientError(Exception):
        pass

    class DummySecretsClient:
        def get_secret_value(self, SecretId):
            if secret_error_message is not None:
                raise DummyClientError(secret_error_message)
            return {"SecretString": secret_payload}

    def client(service_name, region_name=None):
        calls.append((service_name, region_name))
        return DummySecretsClient()

    boto3_module = types.ModuleType("boto3")
    boto3_module.client = client
    botocore_module = types.ModuleType("botocore")
    botocore_exceptions = types.ModuleType("botocore.exceptions")
    botocore_exceptions.BotoCoreError = DummyBotoCoreError
    botocore_exceptions.ClientError = DummyClientError
    botocore_module.exceptions = botocore_exceptions

    monkeypatch.setitem(sys.modules, "boto3", boto3_module)
    monkeypatch.setitem(sys.modules, "botocore", botocore_module)
    monkeypatch.setitem(
        sys.modules,
        "botocore.exceptions",
        botocore_exceptions,
    )

    existing = sys.modules.get("config")
    if existing is None:
        import config as config_module
    else:
        config_module = existing

    if existing is None:
        return config_module, calls

    return importlib.reload(config_module), calls


def test_config_fetches_shared_secret_once_and_reuses_cache(monkeypatch):
    module, calls = _load_config_module(
        monkeypatch,
        env={
            "SECRET_ARN": (
                "arn:aws:secretsmanager:eu-west-3:123456789012:secret:app"
            ),
            "AWS_REGION_NAME": "eu-west-3",
        },
        secret_payload=(
            (
                '{"SECRET_KEY": "prod-secret", '
                '"MSAL_CLIENT_SECRET": "msal-secret"}'
            )
        ),
    )

    assert module.Config.SECRET_KEY == "prod-secret"
    assert module.Config.MSAL_CLIENT_SECRET == "msal-secret"
    assert calls == [("secretsmanager", "eu-west-3")]


def test_config_raises_when_secret_key_cannot_be_loaded_without_env_fallback(
    monkeypatch,
):
    with pytest.raises(
        RuntimeError,
        match="Failed to load application secrets",
    ):
        _load_config_module(
            monkeypatch,
            env={
                "SECRET_ARN": (
                    "arn:aws:secretsmanager:eu-west-3:123456789012:secret:app"
                )
            },
            secret_payload='{"SECRET_KEY": "unused"}',
            secret_error_message="boom",
        )
