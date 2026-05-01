"""Роутер продавца. Реализует UC-6: добавление товара."""
from __future__ import annotations

import secrets
import shutil
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_user
from ..models import Product, ProductStatus, User, UserRole
from ..templating import templates

router = APIRouter(prefix="/seller", tags=["seller"])

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


class _RedirectToLogin(Exception):
    """Контроллер вернёт RedirectResponse на /login, если пользователь не авторизован."""


def _require_seller(user: User | None) -> User:
    if user is None:
        raise _RedirectToLogin
    if user.role != UserRole.SELLER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ только для продавцов.")
    return user


def _save_upload(upload: UploadFile) -> tuple[str | None, str | None]:
    """Сохраняет загруженное фото и возвращает (filename, error)."""
    if upload is None or upload.filename in (None, ""):
        return None, None

    suffix = Path(upload.filename).suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        return None, "Файл должен быть изображением (.jpg, .jpeg, .png, .webp, .gif)."
    if upload.content_type and upload.content_type not in settings.allowed_image_types:
        return None, "Поддерживаются только изображения JPEG, PNG, WebP, GIF."

    upload.file.seek(0, 2)
    size = upload.file.tell()
    upload.file.seek(0)
    if size > settings.max_image_size_bytes:
        max_mb = settings.max_image_size_bytes // (1024 * 1024)
        return None, f"Файл слишком большой (максимум {max_mb} МБ)."
    if size == 0:
        return None, "Файл пуст."

    target_name = f"{secrets.token_hex(16)}{suffix}"
    target_path = settings.uploads_dir / target_name
    with target_path.open("wb") as out:
        shutil.copyfileobj(upload.file, out)
    return target_name, None


def _parse_price(raw: str) -> tuple[Decimal | None, str | None]:
    raw = raw.replace(",", ".").strip()
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError):
        return None, "Цена должна быть числом."
    if value <= 0:
        return None, "Цена должна быть больше 0."
    quantized = value.quantize(Decimal("0.01"))
    return quantized, None


@router.get("", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seller = _require_seller(user)
    products = (
        db.query(Product)
        .filter(Product.seller_id == seller.id)
        .order_by(desc(Product.created_at))
        .limit(6)
        .all()
    )
    counts = {
        ProductStatus.PENDING: 0,
        ProductStatus.PUBLISHED: 0,
        ProductStatus.REJECTED: 0,
    }
    for status_value, in db.query(Product.status).filter(Product.seller_id == seller.id).all():
        counts[status_value] = counts.get(status_value, 0) + 1
    return templates.TemplateResponse(
        request,
        "seller/dashboard.html",
        {"user": seller, "recent_products": products, "counts": counts},
    )


@router.get("/products", response_class=HTMLResponse)
def list_products(
    request: Request,
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seller = _require_seller(user)
    products = (
        db.query(Product)
        .filter(Product.seller_id == seller.id)
        .order_by(desc(Product.created_at))
        .all()
    )
    return templates.TemplateResponse(
        request,
        "seller/products.html",
        {"user": seller, "products": products},
    )


@router.get("/products/new", response_class=HTMLResponse)
def new_product_form(
    request: Request,
    user: User | None = Depends(get_current_user),
):
    seller = _require_seller(user)
    return templates.TemplateResponse(
        request,
        "seller/new_product.html",
        {
            "user": seller,
            "errors": [],
            "form": {"name": "", "price": "", "sizes": "", "description": ""},
        },
    )


@router.post("/products/new", response_class=HTMLResponse)
def create_product(
    request: Request,
    name: str = Form(...),
    price: str = Form(...),
    sizes: str = Form(""),
    description: str = Form(""),
    image: UploadFile = File(None),
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seller = _require_seller(user)
    errors: list[str] = []

    name_clean = name.strip()
    if not name_clean:
        errors.append("Название не может быть пустым.")
    elif len(name_clean) > 160:
        errors.append("Название не должно быть длиннее 160 символов.")

    price_value, price_err = _parse_price(price)
    if price_err:
        errors.append(price_err)

    sizes_clean = ",".join(s.strip() for s in sizes.split(",") if s.strip())
    description_clean = description.strip()

    saved_filename: str | None = None
    if image is not None and image.filename:
        saved_filename, image_err = _save_upload(image)
        if image_err:
            errors.append(image_err)

    if errors:
        return templates.TemplateResponse(
            request,
            "seller/new_product.html",
            {
                "user": seller,
                "errors": errors,
                "form": {
                    "name": name_clean,
                    "price": price,
                    "sizes": sizes,
                    "description": description_clean,
                },
            },
            status_code=400,
        )

    assert price_value is not None
    product = Product(
        name=name_clean,
        description=description_clean,
        price=price_value,
        sizes=sizes_clean,
        image_filename=saved_filename,
        status=ProductStatus.PENDING,
        seller_id=seller.id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return RedirectResponse(url="/seller/products", status_code=303)
