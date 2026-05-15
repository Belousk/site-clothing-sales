"""Корзина покупателя (UC-2)."""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from ...database import get_db
from ...models import CartItem, Product, ProductStatus, User
from ...schemas import (
    CartAddIn,
    CartItemOut,
    CartOut,
    CartUpdateIn,
    MessageResponse,
    ProductOut,
)
from ._common import require_buyer

router = APIRouter(prefix="/cart", tags=["cart"])


def _active_cart(db: Session, buyer_id: int) -> list[CartItem]:
    items = (
        db.query(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.seller))
        .filter(CartItem.buyer_id == buyer_id)
        .all()
    )
    return [item for item in items if item.product.status == ProductStatus.PUBLISHED]


def _build_cart(items: list[CartItem]) -> CartOut:
    total = sum((item.line_total for item in items), Decimal("0.00"))
    return CartOut(
        items=[
            CartItemOut(
                id=i.id,
                product=ProductOut.from_model(i.product),
                quantity=i.quantity,
                line_total=i.line_total,
            )
            for i in items
        ],
        total=total,
        item_count=sum(i.quantity for i in items),
    )


@router.get("", response_model=CartOut)
def view_cart(buyer: User = Depends(require_buyer), db: Session = Depends(get_db)):
    return _build_cart(_active_cart(db, buyer.id))


@router.post("/add", response_model=CartOut)
def add_to_cart(
    payload: CartAddIn,
    buyer: User = Depends(require_buyer),
    db: Session = Depends(get_db),
):
    product = db.get(Product, payload.product_id)
    if product is None or product.status != ProductStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден.")
    if product.stock <= 0:
        raise HTTPException(status_code=400, detail="Товар закончился на складе.")
    existing = (
        db.query(CartItem)
        .filter(CartItem.buyer_id == buyer.id, CartItem.product_id == payload.product_id)
        .first()
    )
    if existing is None:
        qty = min(payload.quantity, product.stock)
        db.add(CartItem(buyer_id=buyer.id, product_id=payload.product_id, quantity=qty))
    else:
        existing.quantity = min(existing.quantity + payload.quantity, 99, product.stock)
    db.commit()
    return _build_cart(_active_cart(db, buyer.id))


@router.post("/{item_id}/update", response_model=CartOut)
def update_quantity(
    item_id: int,
    payload: CartUpdateIn,
    buyer: User = Depends(require_buyer),
    db: Session = Depends(get_db),
):
    item = db.get(CartItem, item_id)
    if item is None or item.buyer_id != buyer.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Позиция не найдена.")
    product = db.get(Product, item.product_id)
    max_qty = min(payload.quantity, product.stock) if product else payload.quantity
    item.quantity = max(1, max_qty)
    db.commit()
    return _build_cart(_active_cart(db, buyer.id))


@router.post("/{item_id}/remove", response_model=CartOut)
def remove_item(
    item_id: int,
    buyer: User = Depends(require_buyer),
    db: Session = Depends(get_db),
):
    item = db.get(CartItem, item_id)
    if item is None or item.buyer_id != buyer.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Позиция не найдена.")
    db.delete(item)
    db.commit()
    return _build_cart(_active_cart(db, buyer.id))


@router.post("/clear", response_model=MessageResponse)
def clear_cart(buyer: User = Depends(require_buyer), db: Session = Depends(get_db)):
    db.query(CartItem).filter(CartItem.buyer_id == buyer.id).delete()
    db.commit()
    return MessageResponse()
