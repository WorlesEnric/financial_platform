from __future__ import annotations

import functools
from typing import Any, Callable, Optional, Sequence

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel

from finance_platform.errors.exceptions import (
    AuthenticationError,
    AuthorizationError,
    PermissionDeniedError,
)


class CompanyContext(BaseModel):
    company_id: str
    user_id: str
    role: str


def _get_context(request: Request) -> CompanyContext:
    user = getattr(request.state, "user", None)
    company_id = getattr(request.state, "company_id", None)
    if not user or not company_id:
        raise AuthenticationError("User or company context not resolved")
    return CompanyContext(
        company_id=company_id,
        user_id=user.get("id", "") if isinstance(user, dict) else str(user.id),
        role=user.get("role", "") if isinstance(user, dict) else getattr(user, "role", ""),
    )


class RoleChecker:
    def __init__(self, allowed_roles: Sequence[str]) -> None:
        self._allowed_roles = set(allowed_roles)

    def __call__(self, context: CompanyContext = Depends(_get_context)) -> bool:
        if context.role not in self._allowed_roles:
            raise PermissionDeniedError(
                f"Role '{context.role}' is not allowed",
                required_role=", ".join(self._allowed_roles),
            )
        return True


def get_current_context(request: Request) -> CompanyContext:
    return _get_context(request)


def require_role(role: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                for val in kwargs.values():
                    if isinstance(val, Request):
                        request = val
                        break
            if request is None:
                raise AuthenticationError("Request object not found")
            user = getattr(request.state, "user", None)
            user_role = (
                user.get("role", "") if isinstance(user, dict) else getattr(user, "role", "")
            )
            if user_role != role:
                raise PermissionDeniedError(
                    f"Required role: {role}, actual: {user_role}",
                    required_role=role,
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_company_role(role: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                for val in kwargs.values():
                    if isinstance(val, Request):
                        request = val
                        break
            if request is None:
                raise AuthenticationError("Request object not found")
            user = getattr(request.state, "user", None)
            company_id = getattr(request.state, "company_id", None)
            if not user or not company_id:
                raise AuthenticationError("User or company context not resolved")
            user_role = (
                user.get("role", "") if isinstance(user, dict) else getattr(user, "role", "")
            )
            if user_role != role:
                raise PermissionDeniedError(
                    f"Required company role: {role}, actual: {user_role}",
                    required_role=role,
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_permission(*permissions: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                for val in kwargs.values():
                    if isinstance(val, Request):
                        request = val
                        break
            if request is None:
                raise AuthenticationError("Request object not found")
            user_permissions = getattr(request.state, "permissions", set())
            missing = [p for p in permissions if p not in user_permissions]
            if missing:
                raise PermissionDeniedError(
                    f"Missing permissions: {', '.join(missing)}",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
