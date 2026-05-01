import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class UserRole(str, enum.Enum):
    """Роли пользователей в системе."""

    BUYER = "buyer"
    SELLER = "seller"
    ADMIN = "admin"


ROLE_LABELS_RU: dict[UserRole, str] = {
    UserRole.BUYER: "Покупатель",
    UserRole.SELLER: "Продавец",
    UserRole.ADMIN: "Администратор",
}


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=16),
        nullable=False,
        default=UserRole.BUYER,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    @property
    def role_label(self) -> str:
        return ROLE_LABELS_RU.get(self.role, self.role.value)
