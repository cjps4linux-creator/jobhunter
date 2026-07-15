from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

from app.auth.models import Token
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def _ensure_bcrypt() -> Any:
    try:
        import bcrypt
    except Exception as exc:
        raise RuntimeError("python 'bcrypt' package is required for auth") from exc
    return bcrypt


def _hash(plain: str) -> str:
    bcrypt = _ensure_bcrypt()
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def _verify(plain: str, hashed: str) -> bool:
    bcrypt = _ensure_bcrypt()
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _now_epoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _create_access_token(subject: str) -> str:
    now = _now_epoch()
    expire = now + (settings.access_token_expire_minutes * 60)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def _create_refresh_token(subject: str, jti: str) -> str:
    now = _now_epoch()
    expire = now + (settings.refresh_token_expire_days * 24 * 60 * 60)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "refresh",
        "jti": jti,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def _decode(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )


_USERS = {
    "user": {
        "username": "user",
        "hashed_password": _hash("password"),
        "role": "user",
        "disabled": False,
    },
    "admin": {
        "username": "admin",
        "hashed_password": _hash("admin"),
        "role": "admin",
        "disabled": False,
    },
}
_REFRESH_JTI: set[str] = set()


def _get_user(username: str) -> dict | None:
    return _USERS.get(username)


def _get_current_user(token: str) -> dict:
    try:
        payload = _decode(token)
        username = payload.get("sub")
        token_type = payload.get("type")
        if not username or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user = _get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


@router.post("/token", response_model=Token)
async def login(username: str = Form(), password: str = Form()):
    user = _get_user(username)
    if not user or not _verify(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    jti = "rt-" + datetime.now(timezone.utc).isoformat()
    access = _create_access_token(user["username"])
    refresh = _create_refresh_token(user["username"], jti)
    _REFRESH_JTI.add(jti)
    return Token(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=Token)
async def refresh(refresh_token: str = Body(embed=True)):
    try:
        payload = _decode(refresh_token)
        username = payload.get("sub")
        jti = payload.get("jti")
        token_type = payload.get("type")
        if (
            not username
            or token_type != "refresh"
            or not jti
            or jti not in _REFRESH_JTI
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or already used",
            )
        _REFRESH_JTI.discard(jti)
        user = _get_user(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        new_jti = "rt-" + datetime.now(timezone.utc).isoformat()
        access = _create_access_token(user["username"])
        refresh = _create_refresh_token(user["username"], new_jti)
        _REFRESH_JTI.add(new_jti)
        return Token(access_token=access, refresh_token=refresh)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.get("/me")
async def me(token: str = Depends(oauth2_scheme)):
    user = _get_current_user(token)
    return {
        "username": user["username"],
        "role": user["role"],
        "disabled": user["disabled"],
    }
