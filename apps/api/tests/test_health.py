from __future__ import annotations

from fastapi.testclient import TestClient
from pydantic import SecretStr

from pool_ensemble.config import Settings
from pool_ensemble.main import create_app


def test_health_returns_ok() -> None:
    client = TestClient(create_app(Settings(app_env="test")))
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_origins_parses_comma_separated_list() -> None:
    settings = Settings(
        app_env="test",
        allowed_origins=" http://localhost:5173 , , https://pool-ensemble.pages.dev ",
    )

    assert settings.cors_origins == [
        "http://localhost:5173",
        "https://pool-ensemble.pages.dev",
    ]


def test_secrets_are_not_exposed_in_repr() -> None:
    riot_sentinel = "test-sentinel-riot-value"
    salt_sentinel = "test-sentinel-salt-value"
    settings = Settings(
        app_env="test",
        riot_api_key=SecretStr(riot_sentinel),
        puuid_hash_salt=SecretStr(salt_sentinel),
    )

    rendered = f"{settings!r} {settings!s}"
    assert riot_sentinel not in rendered
    assert salt_sentinel not in rendered
