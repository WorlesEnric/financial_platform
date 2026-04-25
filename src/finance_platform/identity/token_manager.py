from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from finance_platform.identity.models import MembershipRole


@dataclass
class TokenPayload:
    user_id: str
    company_id: str
    membership_id: str
    membership_role: MembershipRole
    token_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    issued_at: float = field(default_factory=lambda: time.time())
    expires_at: float = field(default_factory=lambda: time.time() + 3600)
    is_refresh: bool = False
    permissions: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def time_to_live(self) -> float:
        return max(0.0, self.expires_at - time.time())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "company_id": self.company_id,
            "membership_id": self.membership_id,
            "membership_role": self.membership_role.value,
            "token_id": self.token_id,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "is_refresh": self.is_refresh,
            "permissions": self.permissions,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TokenPayload:
        return cls(
            user_id=data["user_id"],
            company_id=data["company_id"],
            membership_id=data["membership_id"],
            membership_role=MembershipRole(data["membership_role"]),
            token_id=data.get("token_id", str(uuid.uuid4())),
            issued_at=data.get("issued_at", time.time()),
            expires_at=data.get("expires_at", time.time() + 3600),
            is_refresh=data.get("is_refresh", False),
            permissions=data.get("permissions", {}),
            metadata=data.get("metadata", {}),
        )


class TokenManager:
    def __init__(
        self,
        secret_key: str,
        access_token_ttl_seconds: int = 3600,
        refresh_token_ttl_seconds: int = 86400,
    ) -> None:
        self._secret_key = secret_key
        self._access_token_ttl = access_token_ttl_seconds
        self._refresh_token_ttl = refresh_token_ttl_seconds
        self._blacklisted_tokens: set[str] = set()

    def _sign(self, payload: Dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hmac.new(
            self._secret_key.encode("utf-8"),
            raw.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def create_access_token(self, payload: TokenPayload) -> str:
        payload.issued_at = time.time()
        payload.expires_at = time.time() + self._access_token_ttl
        payload.is_refresh = False
        data = payload.to_dict()
        data["sig"] = self._sign(data)
        return self._encode(data)

    def create_refresh_token(self, payload: TokenPayload) -> str:
        payload.issued_at = time.time()
        payload.expires_at = time.time() + self._refresh_token_ttl
        payload.is_refresh = True
        data = payload.to_dict()
        data["sig"] = self._sign(data)
        return self._encode(data)

    def _encode(self, data: Dict[str, Any]) -> str:
        raw = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return raw  # base64/encoding omitted for clarity; use JWT in production

    def _decode(self, token: str) -> Dict[str, Any]:
        return json.loads(token)

    def verify(self, token: str) -> Optional[TokenPayload]:
        try:
            data = self._decode(token)
            sig = data.pop("sig", None)
            if sig is None:
                return None
            expected = self._sign(data)
            if not hmac.compare_digest(sig, expected):
                return None
            payload = TokenPayload.from_dict(data)
            if payload.is_expired:
                return None
            if payload.token_id in self._blacklisted_tokens:
                return None
            return payload
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        payload = self.verify(refresh_token)
        if payload is None:
            return None
        if not payload.is_refresh:
            return None
        new_payload = TokenPayload(
            user_id=payload.user_id,
            company_id=payload.company_id,
            membership_id=payload.membership_id,
            membership_role=payload.membership_role,
            permissions=payload.permissions,
            metadata=payload.metadata,
        )
        return self.create_access_token(new_payload)

    def revoke(self, token: str) -> bool:
        payload = self.verify(token)
        if payload is None:
            return False
        self._blacklisted_tokens.add(payload.token_id)
        return True

    def create_token_pair(self, payload: TokenPayload) -> Dict[str, str]:
        return {
            "access_token": self.create_access_token(TokenPayload(
                user_id=payload.user_id,
                company_id=payload.company_id,
                membership_id=payload.membership_id,
                membership_role=payload.membership_role,
                permissions=payload.permissions,
                metadata=payload.metadata,
            )),
            "refresh_token": self.create_refresh_token(TokenPayload(
                user_id=payload.user_id,
                company_id=payload.company_id,
                membership_id=payload.membership_id,
                membership_role=payload.membership_role,
                permissions=payload.permissions,
                metadata=payload.metadata,
            )),
            "token_type": "bearer",
            "expires_in": self._access_token_ttl,
        }
