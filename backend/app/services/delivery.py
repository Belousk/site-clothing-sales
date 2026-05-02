"""UC-5: переходы статуса доставки. Общая логика для админа и продавца."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status

from ..models import (
    DELIVERY_STATUS_LABELS_RU,
    DELIVERY_STATUS_ORDER,
    DeliveryStatus,
    Order,
    OrderStatus,
)


def advance_delivery_status(order: Order, raw_status: str) -> None:
    """Передвигает order.delivery_status вперёд по конвейеру.

    Бросает 400/409 при невалидном переходе. Сам коммит делает вызывающий код.
    """
    if order.status != OrderStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Менять статус доставки можно только у оплаченных заказов.",
        )
    try:
        target = DeliveryStatus(raw_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неизвестный статус доставки: {raw_status}.",
        ) from None

    current_idx = DELIVERY_STATUS_ORDER.index(order.delivery_status)
    target_idx = DELIVERY_STATUS_ORDER.index(target)
    if target_idx <= current_idx:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Текущий статус доставки — «{DELIVERY_STATUS_LABELS_RU[order.delivery_status]}». "
                "Перевести его назад нельзя."
            ),
        )

    now = datetime.now(timezone.utc)
    order.delivery_status = target
    order.delivery_updated_at = now
    # UI допускает прыжок из processing сразу в in_transit/delivered.
    # Если перешли через SHIPPED, всё равно бэкфиллим shipped_at —
    # иначе у покупателя в трекере шаг «Передан в доставку» останется
    # пустым между уже завершёнными шагами.
    shipped_idx = DELIVERY_STATUS_ORDER.index(DeliveryStatus.SHIPPED)
    if target_idx >= shipped_idx and order.shipped_at is None:
        order.shipped_at = now
    if target == DeliveryStatus.DELIVERED and order.delivered_at is None:
        order.delivered_at = now
