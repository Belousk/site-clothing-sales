"""Общие зависимости для API: проверки ролей, текущий пользователь и т.п."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status

from ...dependencies import get_current_user
from ...models import User, UserRole


def require_user(user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация.",
        )
    return user


def require_buyer(user: User = Depends(require_user)) -> User:
    if user.role != UserRole.BUYER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ только для покупателей.")
    return user


def require_seller(user: User = Depends(require_user)) -> User:
    if user.role != UserRole.SELLER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ только для продавцов.")
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ только для администраторов.")
    return user
