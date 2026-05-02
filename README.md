# Maison Couture — интернет-магазин одежды

Учебный проект: разделён на **backend (FastAPI, JSON-API)** и
**frontend (React + TypeScript, SPA)**. Авторизация — сессионная (cookie).
По умолчанию используется **SQLite** для удобства запуска; легко
переключается на **PostgreSQL** через `DATABASE_URL`.

## Что реализовано

- **UC-1** — регистрация и вход для трёх ролей (`buyer`, `seller`, `admin`).
  Админ создаётся через CLI-скрипт.
- **UC-2** — публичный каталог опубликованных товаров с поиском по
  названию (регистронезависимый, работает с кириллицей) и корзина
  покупателя (добавить, изменить количество, удалить).
- **UC-3** — оформление заказа со снапшотом товаров, валидацией адреса
  и очисткой корзины.
- **UC-4** — имитация оплаты + PDF-чек (`receipt_number`,
  `transaction_id`, `pdf_url`), скачивание защищено ACL (владелец или
  админ).
- **UC-5** — статусы доставки `processing → shipped → in_transit →
  delivered`. Меняют вперёд админ (любой оплаченный заказ) и продавец
  (только заказы со своими товарами). Покупатель видит трекер на
  странице заказа.
- **UC-6** — добавление товара продавцом (multipart-загрузка фото,
  валидация имени, цены, размеров, описания), редактирование и удаление
  заявки, пока она в статусе `pending`.
- **UC-7** — модерация заявок администратором (одобрение / отказ с
  обязательной причиной).

## Структура репозитория

```
backend/                       # FastAPI: только JSON API + раздача SPA
├── app/
│   ├── main.py                # включает /api/* роутеры и SPA-fallback
│   ├── config.py              # настройки + uploads_dir, receipts_dir
│   ├── database.py            # engine + SessionLocal + init_db
│   ├── models.py              # User, Product, CartItem, Order, OrderItem, Receipt
│   ├── schemas.py             # Pydantic DTO для API
│   ├── security.py            # passlib/bcrypt
│   ├── dependencies.py        # get_current_user (по сессии)
│   ├── routers/api/
│   │   ├── auth.py            # /api/auth/{register,login,logout,me}
│   │   ├── catalog.py         # /api/catalog
│   │   ├── cart.py            # /api/cart
│   │   ├── orders.py          # /api/orders + /receipts/{file}
│   │   ├── seller.py          # /api/seller/*
│   │   └── admin.py           # /api/admin/*
│   └── services/
│       ├── delivery.py        # переходы статусов доставки
│       └── receipts.py        # PDF чека (reportlab)
├── scripts/create_admin.py
├── uploads/                   # фото товаров (раздаётся через /uploads)
├── receipts/                  # PDF-чеки (раздаётся через /receipts ACL)
└── requirements.txt

frontend/                      # Vite + React + TypeScript SPA
├── src/
│   ├── main.tsx, App.tsx
│   ├── auth.tsx               # AuthContext, useAuth
│   ├── api.ts                 # fetch-обёртка с обработкой ошибок
│   ├── types.ts               # mirror of backend/app/schemas.py
│   ├── components/            # Layout, RequireRole, DeliveryTrack, …
│   └── pages/                 # public, buyer, seller, admin
├── vite.config.ts             # dev-прокси /api, /uploads, /receipts → :8000
├── package.json
└── tsconfig.json
```

## Запуск (Windows / PowerShell)

> На macOS/Linux замените `python` → `python3` и используйте
> `source .venv/bin/activate` вместо `.\.venv\Scripts\Activate.ps1`.

### 1. Подтянуть код

```powershell
cd path\to\site-clothing-sales
git checkout main             # или любую другую ветку
git pull origin main
```

### 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt

# По желанию пересоздать БД (после изменения схемы)
del clothing_sales.db

# Создать администратора (нужно один раз)
python -m scripts.create_admin --username admin --email admin@example.com --password "changeme123"

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend поднимется на `http://127.0.0.1:8000` и будет отдавать только
JSON-API + статику (`/uploads`, `/receipts`). Если фронт ещё не
собран и обращаются к корню `/`, вернётся 503 с подсказкой.

### 3. Frontend (новый второй терминал)

```powershell
cd path\to\site-clothing-sales\frontend
npm install
npm run dev
```

Vite поднимется на `http://127.0.0.1:5173` и будет проксировать
`/api`, `/uploads`, `/receipts` на backend `:8000`. Открывать
приложение нужно по адресу Vite: <http://127.0.0.1:5173>.

### Прод-сборка одним процессом

Если нужно запустить всё одним `uvicorn` (без Vite), сначала соберите
фронт:

```powershell
cd frontend
npm install
npm run build           # создаст frontend\dist
```

Затем поднимите backend как обычно — FastAPI начнёт отдавать
`frontend/dist/index.html` и `dist/assets/*` напрямую.

```powershell
cd ..\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Открывайте `http://127.0.0.1:8000`.

## Переменные окружения (опционально)

В `backend/.env` (или системные переменные):

```
APP_NAME=Maison Couture
SECRET_KEY=dev-secret-please-change
DATABASE_URL=sqlite:///./clothing_sales.db
SESSION_MAX_AGE=1209600
UPLOADS_DIR=uploads
RECEIPTS_DIR=receipts
```

Для PostgreSQL:

```
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/clothing_sales
```

## API в двух словах

| Роут | Метод | Кто | Назначение |
|---|---|---|---|
| `/api/auth/register` | POST | гость | регистрация (`buyer`, `seller`) |
| `/api/auth/login` | POST | гость | вход (логин или email + пароль) |
| `/api/auth/logout` | POST | любой | выход |
| `/api/auth/me` | GET | любой | текущий пользователь или `null` |
| `/api/catalog` | GET | любой | список опубликованных товаров (`?q=...`) |
| `/api/catalog/{id}` | GET | любой | карточка товара |
| `/api/cart`, `/api/cart/add`, `/api/cart/{id}/{update|remove}`, `/api/cart/clear` | — | покупатель | корзина |
| `/api/orders`, `/api/orders/checkout`, `/api/orders/{id}/{pay|cancel}` | — | покупатель | заказы и оплата |
| `/receipts/{filename}` | GET | владелец/админ | скачать PDF-чек |
| `/api/seller/dashboard`, `/api/seller/products[...]`, `/api/seller/orders[...]` | — | продавец | UC-6 + UC-5 |
| `/api/admin/dashboard`, `/api/admin/products[...]`, `/api/admin/orders[...]` | — | админ | UC-7 + UC-5 |
| `/api/enums` | GET | любой | словари статусов (для фронта) |

## Что НЕ делалось

- Реальная интеграция с платёжным шлюзом или курьерским API.
- Тесты (TBD).
- Восстановление пароля / смена email.
