from fastapi import APIRouter, Depends, HTTPException, status

from ..config import settings
from ..deps import get_current_user_id, get_user_repo
from ..security import create_token, decode_token, hash_password, verify_password
from .models import LoginRequest, OAuthRequest, RefreshRequest, RegisterRequest, TokenPair, UserOut
from .oauth import get_oauth_verifier

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


@router.post("/oauth/{provider}", response_model=TokenPair)
async def oauth_login(provider: str, body: OAuthRequest, user_repo=Depends(get_user_repo)):
    verifier = get_oauth_verifier(provider)
    if verifier is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"unsupported provider: {provider}")
    try:
        email = await verifier.verify(body.id_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid oauth token")
    user = await user_repo.get_by_email(email)
    if not user:
        user = await user_repo.create({"email": email, "password_hash": ""})
    return _token_pair(user["id"])
