from fastapi import APIRouter, Depends, HTTPException, status

from ..config import settings
from ..deps import get_current_user_id, get_user_repo
from ..security import create_token, decode_token, hash_password, verify_password
from .models import LoginRequest, RefreshRequest, RegisterRequest, TokenPair, UserOut

router = APIRouter()


def _token_pair(user_id: str) -> TokenPair:
    return TokenPair(
        access_token=create_token(user_id, settings.jwt_secret, "access"),
        refresh_token=create_token(user_id, settings.jwt_secret, "refresh"),
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, user_repo=Depends(get_user_repo)):
    if await user_repo.get_by_email(body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already registered")
    await user_repo.create({"email": body.email, "password_hash": hash_password(body.password)})
    return {"status": "created"}


@router.post("/login", response_model=TokenPair)
async def login(body: LoginRequest, user_repo=Depends(get_user_repo)):
    user = await user_repo.get_by_email(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid email or password")
    return _token_pair(user["id"])


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshRequest, user_repo=Depends(get_user_repo)):
    try:
        user_id = decode_token(body.refresh_token, settings.jwt_secret, "refresh")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired refresh token")
    if not await user_repo.get_by_id(user_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user no longer exists")
    return _token_pair(user_id)


@router.get("/me", response_model=UserOut)
async def me(user_id: str = Depends(get_current_user_id), user_repo=Depends(get_user_repo)):
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user no longer exists")
    return UserOut(id=user["id"], email=user["email"])
