import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class ProductStatus(str, enum.Enum):
    """Статус заявки на публикацию товара (UC-6 / UC-7)."""

    PENDING = "pending"
    PUBLISHED = "published"
    REJECTED = "rejected"


PRODUCT_STATUS_LABELS_RU: dict[ProductStatus, str] = {
    ProductStatus.PENDING: "На модерации",
    ProductStatus.PUBLISHED: "Опубликован",
    ProductStatus.REJECTED: "Отклонён",
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

    products: Mapped[list["Product"]] = relationship(
        back_populates="seller",
        cascade="all, delete-orphan",
    )
    cart_items: Mapped[list["CartItem"]] = relationship(
        back_populates="buyer",
        cascade="all, delete-orphan",
    )

    @property
    def role_label(self) -> str:
        return ROLE_LABELS_RU.get(self.role, self.role.value)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sizes: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    image_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, native_enum=False, length=16),
        nullable=False,
        default=ProductStatus.PENDING,
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    seller_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    seller: Mapped[User] = relationship(back_populates="products")

    @property
    def status_label(self) -> str:
        return PRODUCT_STATUS_LABELS_RU.get(self.status, self.status.value)

    @property
    def sizes_list(self) -> list[str]:
        return [s.strip() for s in self.sizes.split(",") if s.strip()]


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("buyer_id", "product_id", name="uq_cart_buyer_product"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    buyer: Mapped[User] = relationship(back_populates="cart_items")
    product: Mapped[Product] = relationship()

    @property
    def line_total(self) -> Decimal:
        return (self.product.price * self.quantity).quantize(Decimal("0.01"))
