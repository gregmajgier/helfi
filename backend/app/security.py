from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
import jwt

ACCESS_TOKEN_MINUTES = 15
REFRESH_TOKEN_DAYS = 30
ALGORITHM = "HS256"

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_token(user_id: str, secret: str, token_type: TokenType) -> str:
    now = datetime.now(timezone.utc)
    expires = now + (
        timedelta(minutes=ACCESS_TOKEN_MINUTES)
        if token_type == "access"
        else timedelta(days=REFRESH_TOKEN_DAYS)
    )
    payload = {"sub": user_id, "type": token_type, "iat": now, "exp": expires}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str, secret: str, expected_type: TokenType) -> str:
    payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    if payload.get("type") != expected_type:
        raise ValueError(f"expected a {expected_type} token")
    return payload["sub"]
