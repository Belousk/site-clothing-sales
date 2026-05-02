"""API администратора: модерация (UC-7) и управление доставкой (UC-5)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, selectinload

from ...database import get_db
from ...models import (
    Order,
    OrderStatus,
    Product,
    ProductStatus,
    User,
)
from ...schemas import (
    AdminCountsOut,
    DeliveryUpdateIn,
    OrderOut,
    ProductOut,
    RejectIn,
)
from ...services.delivery import advance_delivery_status
from ._common import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


def _status_counts(db: Session) -> dict[ProductStatus, int]:
    rows = db.query(Product.status, func.count(Product.id)).group_by(Product.status).all()
    counts = {s: 0 for s in ProductStatus}
    for status_value, count in rows:
        counts[status_value] = count
    return counts


@router.get("/dashboard", response_model=AdminCountsOut)
def dashboard(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    counts = _status_counts(db)
    total_users = db.query(func.count(User.id)).scalar() or 0
    return AdminCountsOut(
        pending=counts.get(ProductStatus.PENDING, 0),
        published=counts.get(ProductStatus.PUBLISHED, 0),
        rejected=counts.get(ProductStatus.REJECTED, 0),
        total_users=total_users,
    )


@router.get("/products", response_model=list[ProductOut])
def list_products(
    status_filter: str = Query("pending", alias="status"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    valid = {s.value for s in ProductStatus} | {"all"}
    if status_filter not in valid:
        status_filter = "pending"
    query = db.query(Product).options(selectinload(Product.seller))
    if status_filter != "all":
        query = query.filter(Product.status == ProductStatus(status_filter))
    products = query.order_by(desc(Product.created_at)).all()
    return [ProductOut.from_model(p) for p in products]


@router.get("/products/{product_id}", response_model=ProductOut)
def product_detail(product_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .options(selectinload(Product.seller))
        .filter(Product.id == product_id)
        .first()
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден.")
    return ProductOut.from_model(product)


@router.post("/products/{product_id}/approve", response_model=ProductOut)
def approve_product(product_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден.")
    if product.status != ProductStatus.PENDING:
        raise HTTPException(status_code=409, detail="Можно одобрять только заявки в статусе «На модерации».")
    product.status = ProductStatus.PUBLISHED
    product.rejection_reason = None
    db.commit()
    db.refresh(product)
    return ProductOut.from_model(product)


@router.post("/products/{product_id}/reject", response_model=ProductOut)
def reject_product(
    product_id: int,
    payload: RejectIn,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .options(selectinload(Product.seller))
        .filter(Product.id == product_id)
        .first()
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден.")
    if product.status != ProductStatus.PENDING:
        raise HTTPException(status_code=409, detail="Можно отклонять только заявки в статусе «На модерации».")
    reason_clean = payload.reason.strip()
    if not reason_clean:
        raise HTTPException(status_code=400, detail="Укажите причину отказа.")
    if len(reason_clean) > 500:
        raise HTTPException(status_code=400, detail="Причина не должна быть длиннее 500 символов.")
    product.status = ProductStatus.REJECTED
    product.rejection_reason = reason_clean
    db.commit()
    db.refresh(product)
    return ProductOut.from_model(product)


# ---------- UC-5 ----------


@router.get("/orders", response_model=list[OrderOut])
def list_orders(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    orders = (
        db.query(Order)
        .options(selectinload(Order.buyer), selectinload(Order.items), selectinload(Order.receipt))
        .filter(Order.status == OrderStatus.PAID)
        .order_by(desc(Order.created_at))
        .all()
    )
    return [OrderOut.from_model(o, include_buyer=True) for o in orders]


@router.post("/orders/{order_id}/delivery", response_model=OrderOut)
def update_admin_delivery(
    order_id: int,
    payload: DeliveryUpdateIn,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.receipt), selectinload(Order.buyer))
        .filter(Order.id == order_id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Заказ не найден.")
    advance_delivery_status(order, payload.delivery_status.value)
    db.commit()
    db.refresh(order)
    return OrderOut.from_model(order, include_buyer=True)
