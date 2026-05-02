"""Сборка всех API-роутеров под /api."""
from fastapi import APIRouter

from ...schemas import EnumsOut, build_enums
from . import admin as admin_api
from . import auth as auth_api
from . import cart as cart_api
from . import catalog as catalog_api
from . import orders as orders_api
from . import seller as seller_api

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_api.router)
api_router.include_router(catalog_api.router)
api_router.include_router(cart_api.router)
api_router.include_router(orders_api.router)
api_router.include_router(seller_api.router)
api_router.include_router(admin_api.router)


@api_router.get("/enums", response_model=EnumsOut, tags=["meta"])
def get_enums() -> EnumsOut:
    """Перечисления (статусы доставки, заказа, ролей) для фронта."""
    return build_enums()


# Скачивание чеков идёт без префикса /api/, под /receipts/, как раньше.
receipts_router = orders_api.receipts_router

__all__ = ["api_router", "receipts_router"]
