import pytest

from app.security import create_token, decode_token, hash_password, verify_password


def test_hash_password_and_verify_roundtrip():
    hashed = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_create_and_decode_access_token_roundtrip():
    token = create_token("user-123", "test-secret", "access")

    assert decode_token(token, "test-secret", "access") == "user-123"


def test_decode_token_rejects_wrong_type():
    token = create_token("user-123", "test-secret", "refresh")

    with pytest.raises(Exception):
        decode_token(token, "test-secret", "access")


def test_decode_token_rejects_wrong_secret():
    token = create_token("user-123", "test-secret", "access")

    with pytest.raises(Exception):
        decode_token(token, "different-secret", "access")
