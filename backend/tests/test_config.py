import pytest

from app.config import DEFAULT_JWT_SECRET, Settings, validate_production_settings


def test_production_with_default_secret_raises():
    settings = Settings(environment="production", jwt_secret=DEFAULT_JWT_SECRET, db_backend="cosmos")

    with pytest.raises(RuntimeError):
        validate_production_settings(settings)


def test_production_with_memory_backend_raises():
    settings = Settings(environment="production", jwt_secret="a-real-secret", db_backend="memory")

    with pytest.raises(RuntimeError):
        validate_production_settings(settings)


def test_production_with_everything_set_does_not_raise():
    settings = Settings(environment="production", jwt_secret="a-real-secret", db_backend="cosmos")

    validate_production_settings(settings)


def test_development_with_defaults_does_not_raise():
    settings = Settings(environment="development")

    validate_production_settings(settings)
