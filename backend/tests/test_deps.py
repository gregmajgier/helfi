import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.config import settings
from app.deps import get_current_user_id
from app.security import create_token


async def test_get_current_user_id_returns_subject_for_valid_token():
    token = create_token("user-123", settings.jwt_secret, "access")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    assert await get_current_user_id(credentials) == "user-123"


async def test_get_current_user_id_rejects_garbage_token():
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="garbage")

    with pytest.raises(HTTPException):
        await get_current_user_id(credentials)


async def test_get_current_user_id_rejects_refresh_token():
    token = create_token("user-123", settings.jwt_secret, "refresh")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException):
        await get_current_user_id(credentials)
