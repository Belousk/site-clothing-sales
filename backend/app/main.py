"""Точка входа FastAPI: монтирует API + раздаёт SPA (frontend/dist)."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .database import init_db
from .routers.api import api_router, receipts_router

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=settings.session_max_age,
    same_site="lax",
    https_only=False,
)

app.mount("/uploads", StaticFiles(directory=str(settings.uploads_dir)), name="uploads")

app.include_router(api_router)
app.include_router(receipts_router)


@app.get("/healthz", tags=["meta"])
def healthz() -> dict[str, str]:
    return {"status": "ok"}


# ---------- SPA ----------
#
# В dev-режиме фронт обслуживает Vite (npm run dev), а Vite проксирует
# /api, /uploads, /receipts на FastAPI. В этом случае FRONTEND_DIST
# ещё не собран и эти роуты ничего не отдают, но 404 покажет понятное
# сообщение.
#
# В prod-режиме перед запуском uvicorn собирают frontend (npm run build),
# и FastAPI начинает раздавать static + index.html для всех остальных
# путей (SPA fallback).

INDEX_HTML = FRONTEND_DIST / "index.html"
ASSETS_DIR = FRONTEND_DIST / "assets"

if ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


@app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
def spa_fallback(full_path: str):
    # API/служебные пути обработаны выше; сюда они не доходят (FastAPI
    # подбирает более специфичный роут). Но если кто-то попал — 404.
    if full_path.startswith(("api/", "uploads/", "receipts/", "assets/")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML))
    # Frontend ещё не собран — показываем подсказку.
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "Фронтенд не собран. Запустите `npm install` и `npm run dev` "
                "в каталоге frontend/, либо `npm run build` для прод-сборки."
            )
        },
    )
