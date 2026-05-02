"""Публичный каталог опубликованных товаров (UC-2)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, selectinload

from ...database import get_db
from ...models import Product, ProductStatus
from ...schemas import ProductOut

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("", response_model=list[ProductOut])
def list_catalog(q: str = Query("", description="Поиск по названию"), db: Session = Depends(get_db)):
    query = (
        db.query(Product)
        .options(selectinload(Product.seller))
        .filter(Product.status == ProductStatus.PUBLISHED)
    )
    q_clean = q.strip()
    if q_clean:
        needle = f"%{q_clean.lower()}%"
        query = query.filter(func.lower(Product.name).like(needle))
    products = query.order_by(desc(Product.created_at)).all()
    return [ProductOut.from_model(p) for p in products]


@router.get("/{product_id}", response_model=ProductOut)
def catalog_detail(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .options(selectinload(Product.seller))
        .filter(Product.id == product_id, Product.status == ProductStatus.PUBLISHED)
        .first()
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден.")
    return ProductOut.from_model(product)
