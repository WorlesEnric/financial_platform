from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt as pyjwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from finance_platform.errors.exceptions import AuthenticationError

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class TokenPayload(BaseModel):
    sub: str
    company_id: Optional[str] = None
    role: Optional[str] = None
    exp: int
    iat: int
    jti: str = ""


def get_jwt_secret() -> str:
    from finance_platform.config import get_settings

    return get_settings().JWT_SECRET


class JWTManager:
    def __init__(self, secret: Optional[str] = None) -> None:
        self._secret = secret or get_jwt_secret()

    def encode(self, payload: dict) -> str:
        return pyjwt.encode(payload, self._secret, algorithm=ALGORITHM)

    def decode(self, token: str) -> dict:
        try:
            return pyjwt.decode(token, self._secret, algorithms=[ALGORITHM])
        except pyjwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except pyjwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")


_jwt_manager: Optional[JWTManager] = None


def get_jwt_manager() -> JWTManager:
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager


def create_access_token(
    user_id: str,
    company_id: Optional[str] = None,
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    manager = get_jwt_manager()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": user_id,
        "company_id": company_id or "",
        "role": role or "",
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return manager.encode(payload)


def create_refresh_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    manager = get_jwt_manager()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return manager.encode(payload)


def decode_token(token: str) -> TokenPayload:
    manager = get_jwt_manager()
    data = manager.decode(token)
    return TokenPayload(
        sub=data.get("sub", ""),
        company_id=data.get("company_id"),
        role=data.get("role"),
        exp=data.get("exp", 0),
        iat=data.get("iat", 0),
        jti=data.get("jti", ""),
    )


_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
) -> dict:
    if credentials is None:
        raise AuthenticationError("Not authenticated")
    payload = decode_token(credentials.credentials)
    return {
        "id": payload.sub,
        "company_id": payload.company_id,
        "role": payload.role,
    }


class JWTBearer:
    def __init__(self, auto_error: bool = True) -> None:
        self._auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[dict]:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            if self._auto_error:
                raise AuthenticationError("Missing or invalid authorization header")
            return None
        token = auth[7:]
        try:
            payload = decode_token(token)
            return {
                "id": payload.sub,
                "company_id": payload.company_id,
                "role": payload.role,
            }
        except AuthenticationError:
            if self._auto_error:
                raise
            return None
