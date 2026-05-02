"""API авторизации: регистрация, логин, логаут, текущий пользователь."""
from __future__ import annotations

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ...database import get_db
from ...dependencies import get_current_user
from ...models import User, UserRole
from ...schemas import LoginIn, MessageResponse, RegisterIn, UserOut
from ...security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

ALLOWED_REGISTER_ROLES = {UserRole.BUYER, UserRole.SELLER}


@router.get("/me", response_model=UserOut | None)
def me(user: User | None = Depends(get_current_user)):
    if user is None:
        return None
    return UserOut.from_model(user)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, request: Request, db: Session = Depends(get_db)):
    username = payload.username.strip()
    email = payload.email.strip().lower()

    if len(username) < 3 or len(username) > 64:
        raise HTTPException(status_code=400, detail="Логин должен быть от 3 до 64 символов.")
    try:
        email = validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Введите корректный email.") from None
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Пароль должен быть не короче 6 символов.")
    if payload.password != payload.password_confirm:
        raise HTTPException(status_code=400, detail="Пароли не совпадают.")
    if payload.role not in ALLOWED_REGISTER_ROLES:
        raise HTTPException(status_code=400, detail="Регистрация администратора через форму недоступна.")

    existing = (
        db.query(User)
        .filter(or_(User.username == username, User.email == email))
        .first()
    )
    if existing is not None:
        if existing.username == username:
            raise HTTPException(status_code=400, detail="Логин уже используется.")
        raise HTTPException(status_code=400, detail="Email уже используется.")

    new_user = User(
        username=username,
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    request.session["user_id"] = new_user.id
    return UserOut.from_model(new_user)


@router.post("/login", response_model=UserOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    identifier = payload.identifier.strip()
    candidate = (
        db.query(User)
        .filter(or_(User.username == identifier, User.email == identifier.lower()))
        .first()
    )
    if candidate is None or not verify_password(payload.password, candidate.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин/email или пароль.")
    request.session["user_id"] = candidate.id
    return UserOut.from_model(candidate)


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request):
    request.session.clear()
    return MessageResponse()
