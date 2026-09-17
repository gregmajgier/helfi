import pytest

from app.auth import oauth
from app.config import settings


@pytest.fixture()
def restore_settings():
    original_environment = settings.environment
    original_google_client_id = settings.google_oauth_client_id
    original_apple_bundle_id = settings.apple_oauth_bundle_id
    yield
    settings.environment = original_environment
    settings.google_oauth_client_id = original_google_client_id
    settings.apple_oauth_bundle_id = original_apple_bundle_id
    oauth.reset_oauth_verifier_cache()


def test_google_verifier_unavailable_in_production_without_client_id(restore_settings):
    settings.environment = "production"
    settings.google_oauth_client_id = None
    oauth.reset_oauth_verifier_cache()

    assert oauth.get_oauth_verifier("google") is None


def test_apple_verifier_unavailable_in_production_without_bundle_id(restore_settings):
    settings.environment = "production"
    settings.apple_oauth_bundle_id = None
    oauth.reset_oauth_verifier_cache()

    assert oauth.get_oauth_verifier("apple") is None


def test_fake_verifier_used_in_development_without_credentials(restore_settings):
    settings.environment = "development"
    settings.google_oauth_client_id = None
    oauth.reset_oauth_verifier_cache()

    verifier = oauth.get_oauth_verifier("google")

    assert verifier is not None
    assert isinstance(verifier, oauth.FakeOAuthVerifier)
