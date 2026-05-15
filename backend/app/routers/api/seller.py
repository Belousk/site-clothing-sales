"""API продавца: товары (CRUD pending) и заказы/доставка."""
from __future__ import annotations

import json
import re
import secrets
import shutil
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from ...config import settings
from ...database import get_db
from ...models import (
    Order,
    OrderItem,
    OrderStatus,
    Product,
    ProductStatus,
    ProductVariant,
    User,
)
from ...schemas import DeliveryUpdateIn, MessageResponse, OrderOut, ProductOut
from ...services.delivery import advance_delivery_status
from ._common import require_seller

router = APIRouter(prefix="/seller", tags=["seller"])

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

NAME_MAX_LENGTH = 160
DESCRIPTION_MAX_LENGTH = 4000
SIZES_MAX_COUNT = 20
SIZE_MIN_LENGTH = 1
SIZE_MAX_LENGTH = 8
_SIZE_PATTERN = re.compile(r"^[A-Za-zА-Яа-яЁё0-9\.\- ]+$")


def _save_upload(upload: UploadFile | None) -> str | None:
    """Сохраняет загруженное фото и возвращает имя файла либо бросает 400."""
    if upload is None or not upload.filename:
        return None
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Файл должен быть изображением (.jpg, .jpeg, .png, .webp, .gif).")
    if upload.content_type and upload.content_type not in settings.allowed_image_types:
        raise HTTPException(status_code=400, detail="Поддерживаются только изображения JPEG, PNG, WebP, GIF.")

    upload.file.seek(0, 2)
    size = upload.file.tell()
    upload.file.seek(0)
    if size > settings.max_image_size_bytes:
        max_mb = settings.max_image_size_bytes // (1024 * 1024)
        raise HTTPException(status_code=400, detail=f"Файл слишком большой (максимум {max_mb} МБ).")
    if size == 0:
        raise HTTPException(status_code=400, detail="Файл пуст.")

    target_name = f"{secrets.token_hex(16)}{suffix}"
    target_path = settings.uploads_dir / target_name
    with target_path.open("wb") as out:
        shutil.copyfileobj(upload.file, out)
    return target_name


def _parse_price(raw: str) -> Decimal:
    raw = raw.replace(",", ".").strip()
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError):
        raise HTTPException(status_code=400, detail="Цена должна быть числом.") from None
    if value <= 0:
        raise HTTPException(status_code=400, detail="Цена должна быть больше 0.")
    return value.quantize(Decimal("0.01"))


def _validate_sizes(raw: str) -> str:
    items = [s.strip() for s in raw.split(",") if s.strip()]
    if len(items) > SIZES_MAX_COUNT:
        raise HTTPException(status_code=400, detail=f"Слишком много размеров — максимум {SIZES_MAX_COUNT}.")
    seen: set[str] = set()
    cleaned: list[str] = []
    for s in items:
        if len(s) < SIZE_MIN_LENGTH or len(s) > SIZE_MAX_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Размер «{s}» должен быть от {SIZE_MIN_LENGTH} до {SIZE_MAX_LENGTH} символов.",
            )
        if not _SIZE_PATTERN.match(s):
            raise HTTPException(
                status_code=400,
                detail=f"Размер «{s}» может содержать только буквы, цифры, точку, дефис и пробел.",
            )
        key = s.upper()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(s)
    return ", ".join(cleaned)


def _parse_size_stocks(raw: str) -> dict[str, int]:
    """Parse JSON string like {"S": 5, "M": 3} into validated size→stock mapping."""
    raw = raw.strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Неверный формат остатков по размерам.") from None
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Остатки по размерам должны быть объектом.")
    if len(data) > SIZES_MAX_COUNT:
        raise HTTPException(status_code=400, detail=f"Слишком много размеров — максимум {SIZES_MAX_COUNT}.")
    result: dict[str, int] = {}
    seen: set[str] = set()
    for size_key, stock_val in data.items():
        size_str = str(size_key).strip()
        if not size_str or len(size_str) > SIZE_MAX_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Размер «{size_str}» должен быть от {SIZE_MIN_LENGTH} до {SIZE_MAX_LENGTH} символов.",
            )
        if not _SIZE_PATTERN.match(size_str):
            raise HTTPException(
                status_code=400,
                detail=f"Размер «{size_str}» может содержать только буквы, цифры, точку, дефис и пробел.",
            )
        try:
            stock_int = int(stock_val)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"Остаток для размера «{size_str}» должен быть целым числом.") from None
        if stock_int < 0:
            raise HTTPException(status_code=400, detail=f"Остаток для размера «{size_str}» не может быть отрицательным.")
        upper = size_str.upper()
        if upper in seen:
            continue
        seen.add(upper)
        result[size_str] = stock_int
    return result


@dataclass
class _ProductInput:
    name: str
    price: Decimal
    description: str
    size_stocks: dict[str, int] = field(default_factory=dict)


def _validate_basic(name: str, price: str, description: str, size_stocks: str) -> _ProductInput:
    name_clean = name.strip()
    if not name_clean:
        raise HTTPException(status_code=400, detail="Название не может быть пустым.")
    if len(name_clean) > NAME_MAX_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Название не должно быть длиннее {NAME_MAX_LENGTH} символов.",
        )
    price_value = _parse_price(price)
    description_clean = description.strip()
    if len(description_clean) > DESCRIPTION_MAX_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Описание не должно быть длиннее {DESCRIPTION_MAX_LENGTH} символов.",
        )
    parsed_sizes = _parse_size_stocks(size_stocks)
    return _ProductInput(name_clean, price_value, description_clean, parsed_sizes)


def _own_product_or_404(db: Session, seller: User, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None or product.seller_id != seller.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден.")
    return product


@router.get("/dashboard")
def dashboard(seller: User = Depends(require_seller), db: Session = Depends(get_db)):
    counts = {ProductStatus.PENDING: 0, ProductStatus.PUBLISHED: 0, ProductStatus.REJECTED: 0}
    for status_value, in db.query(Product.status).filter(Product.seller_id == seller.id).all():
        counts[status_value] = counts.get(status_value, 0) + 1
    recent = (
        db.query(Product)
        .options(selectinload(Product.variants))
        .filter(Product.seller_id == seller.id)
        .order_by(desc(Product.created_at))
        .limit(6)
        .all()
    )
    return {
        "counts": {k.value: v for k, v in counts.items()},
        "recent": [ProductOut.from_model(p) for p in recent],
    }


@router.get("/products", response_model=list[ProductOut])
def list_products(seller: User = Depends(require_seller), db: Session = Depends(get_db)):
    products = (
        db.query(Product)
        .options(selectinload(Product.variants))
        .filter(Product.seller_id == seller.id)
        .order_by(desc(Product.created_at))
        .all()
    )
    return [ProductOut.from_model(p) for p in products]


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, seller: User = Depends(require_seller), db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .options(selectinload(Product.variants))
        .filter(Product.id == product_id, Product.seller_id == seller.id)
        .first()
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден.")
    return ProductOut.from_model(product)


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    name: str = Form(...),
    price: str = Form(...),
    description: str = Form(""),
    size_stocks: str = Form("{}"),
    image: UploadFile = File(None),
    seller: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    data = _validate_basic(name, price, description, size_stocks)
    saved_filename = _save_upload(image)

    sizes_str = ", ".join(data.size_stocks.keys())
    total_stock = sum(data.size_stocks.values())
    product = Product(
        name=data.name,
        description=data.description,
        price=data.price,
        sizes=sizes_str,
        stock=total_stock,
        image_filename=saved_filename,
        status=ProductStatus.PENDING,
        seller_id=seller.id,
    )
    db.add(product)
    db.flush()
    for size, stock_qty in data.size_stocks.items():
        db.add(ProductVariant(product_id=product.id, size=size, stock=stock_qty))
    db.commit()
    db.refresh(product)
    return ProductOut.from_model(product)


@router.post("/products/{product_id}/edit", response_model=ProductOut)
def edit_product(
    product_id: int,
    name: str = Form(...),
    price: str = Form(...),
    description: str = Form(""),
    size_stocks: str = Form("{}"),
    image: UploadFile = File(None),
    remove_image: str = Form(""),
    seller: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    product = _own_product_or_404(db, seller, product_id)
    if product.status != ProductStatus.PENDING:
        raise HTTPException(status_code=409, detail="Редактировать можно только товары в статусе «На модерации».")

    data = _validate_basic(name, price, description, size_stocks)
    new_filename = _save_upload(image)

    old_filename = product.image_filename
    product.name = data.name
    product.price = data.price
    product.description = data.description
    product.sizes = ", ".join(data.size_stocks.keys())
    product.stock = sum(data.size_stocks.values())

    db.query(ProductVariant).filter(ProductVariant.product_id == product.id).delete()
    for size, stock_qty in data.size_stocks.items():
        db.add(ProductVariant(product_id=product.id, size=size, stock=stock_qty))

    image_changed = False
    if new_filename is not None:
        product.image_filename = new_filename
        image_changed = True
    elif remove_image == "1":
        product.image_filename = None
        image_changed = True
    db.commit()
    if image_changed and old_filename:
        (settings.uploads_dir / old_filename).unlink(missing_ok=True)
    db.refresh(product)
    return ProductOut.from_model(product)


@router.post("/products/{product_id}/delete", response_model=MessageResponse)
def delete_product(
    product_id: int,
    seller: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    product = _own_product_or_404(db, seller, product_id)
    if product.status != ProductStatus.PENDING:
        raise HTTPException(status_code=409, detail="Удалять можно только товары в статусе «На модерации».")
    old_filename = product.image_filename
    db.delete(product)
    db.commit()
    if old_filename:
        (settings.uploads_dir / old_filename).unlink(missing_ok=True)
    return MessageResponse()


# ---------- Доставка ----------


def _orders_with_seller_items(db: Session, seller_id: int) -> list[Order]:
    return (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.receipt), selectinload(Order.buyer))
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, OrderItem.product_id == Product.id)
        .filter(Product.seller_id == seller_id)
        .filter(Order.status == OrderStatus.PAID)
        .order_by(desc(Order.created_at))
        .distinct()
        .all()
    )


def _seller_owns_order(db: Session, seller_id: int, order: Order) -> bool:
    return (
        db.query(OrderItem)
        .join(Product, OrderItem.product_id == Product.id)
        .filter(OrderItem.order_id == order.id, Product.seller_id == seller_id)
        .first()
        is not None
    )


@router.get("/orders", response_model=list[OrderOut])
def list_seller_orders(seller: User = Depends(require_seller), db: Session = Depends(get_db)):
    orders = _orders_with_seller_items(db, seller.id)
    return [OrderOut.from_model(o, include_buyer=True) for o in orders]


@router.post("/orders/{order_id}/delivery", response_model=OrderOut)
def update_seller_delivery(
    order_id: int,
    payload: DeliveryUpdateIn,
    seller: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.receipt), selectinload(Order.buyer))
        .filter(Order.id == order_id)
        .first()
    )
    if order is None or not _seller_owns_order(db, seller.id, order):
        raise HTTPException(status_code=404, detail="Заказ не найден.")
    advance_delivery_status(order, payload.delivery_status.value)
    db.commit()
    db.refresh(order)
    return OrderOut.from_model(order, include_buyer=True)
