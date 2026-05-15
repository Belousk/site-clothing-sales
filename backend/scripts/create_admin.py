"""Скрипт для создания администратора из CLI.

Использование:
    python -m scripts.create_admin --username admin --email admin@example.com --password 'secret123'
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, init_db  # noqa: E402
from app.models import User, UserRole  # noqa: E402
from app.security import hash_password  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Создать пользователя-администратора")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        existing = (
            db.query(User)
            .filter((User.username == args.username) | (User.email == args.email.lower()))
            .first()
        )
        if existing is not None:
            print(f"Пользователь '{existing.username}' уже существует (id={existing.id}).")
            return 1
        admin = User(
            username=args.username,
            email=args.email.lower(),
            password_hash=hash_password(args.password),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"Создан администратор: {admin.username} <{admin.email}> (id={admin.id})")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
