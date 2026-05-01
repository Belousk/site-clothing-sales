# Atelier — интернет-магазин одежды

Учебный проект информационной системы интернет-магазина одежды.
Реализован на **Python (FastAPI)** с использованием **Jinja2** шаблонов и
**SQLAlchemy** в качестве ORM. По умолчанию используется **SQLite** для удобства
запуска; для продакшена/учебных целей легко переключается на **PostgreSQL**.

## Что уже реализовано

- Главная страница с описанием возможностей системы для трёх ролей.
- Регистрация и вход для покупателя и продавца (роли `buyer`, `seller`).
- Вход для администратора (роль `admin`, заводится через CLI-скрипт).
- Сессионная аутентификация (cookie + подпись).
- Личные кабинеты для каждой роли с переходами по ролям.
- **UC-6: Добавление товара продавцом** — форма с валидацией (название
  непустое, цена &gt; 0), загрузка фото (JPEG/PNG/WebP/GIF до 5 МБ),
  размеры через запятую. Товары создаются со статусом «На модерации».
- Список «Мои товары» для продавца со статусами модерации и причиной
  отказа (если заявка отклонена).
- **UC-7: Модерация заявок администратором** — список заявок с фильтрами
  по статусу, детальная карточка с действиями «Одобрить» / «Отклонить»
  (с обязательным указанием причины). Одобрение переводит товар в
  статус «Опубликован», отказ — в «Отклонён».

Дальнейшие модули (UC-2 каталог/корзина, UC-3 оформление заказа,
UC-4 оплата, UC-5 отслеживание доставки) будут реализованы в
следующих итерациях.

## Структура

```
backend/
├── app/
│   ├── main.py            # FastAPI приложение
│   ├── config.py          # Настройки (pydantic-settings) + uploads_dir
│   ├── database.py        # Engine + SessionLocal + init_db
│   ├── models.py          # User, UserRole, Product, ProductStatus
│   ├── security.py        # passlib/bcrypt
│   ├── dependencies.py    # get_current_user
│   ├── templating.py      # Jinja2Templates
│   ├── routers/
│   │   ├── pages.py       # /, /account
│   │   ├── auth.py        # /register, /login, /logout
│   │   ├── seller.py      # /seller, /seller/products[/new]
│   │   └── admin.py       # /admin, /admin/products[/{id}{/approve|/reject}]
│   ├── templates/
│   │   ├── base.html, index.html, login.html, register.html, buyer.html
│   │   ├── seller/        # dashboard, new_product, products
│   │   └── admin/         # dashboard, products_list, product_detail
│   └── static/styles.css  # Премиум-минимал стили
├── scripts/create_admin.py
├── uploads/               # фото товаров (раздаётся через /uploads)
├── requirements.txt
└── .env.example
```

## Быстрый запуск (рекомендуется)

Минимальные требования: **Python 3.10+**.

```bash
git clone https://github.com/hruphel/site-clothing-sales.git
cd site-clothing-sales/backend

# 1. Виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# 2. Зависимости
pip install --upgrade pip
pip install -r requirements.txt

# 3. (опционально) собственные настройки
cp .env.example .env

# 4. Запуск dev-сервера
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

После старта откройте http://127.0.0.1:8000 — увидите главную страницу.

База данных SQLite (`backend/clothing_sales.db`) и таблицы создаются
автоматически при первом запуске.

## Создание администратора

Регистрация администратора через форму намеренно отключена. Заведите
аккаунт администратора через CLI-скрипт (запускать из директории `backend/`):

```bash
python -m scripts.create_admin \
    --username admin \
    --email admin@example.com \
    --password 'changeme123'
```

После этого войдите на `/login` под этим логином — система перенаправит
в `/admin`.

## Как проверить все три роли

1. Зарегистрируйтесь на `/register`, выбрав «Покупатель» — вы попадёте
   на `/account`.
2. Выйдите, зарегистрируйтесь повторно с другим логином и ролью «Продавец»
   — попадёте на `/seller`. Откройте `/seller/products/new`, добавьте
   товар (название, цена, размеры, фото) — он появится в `/seller/products`
   со статусом «На модерации».
3. Создайте администратора через `scripts/create_admin.py` и войдите
   на `/login` — попадёте на `/admin`.

## UC-6: добавление товара (продавец)

- `GET /seller/products/new` — форма добавления (только для роли
  `seller`).
- `POST /seller/products/new` — `multipart/form-data` с полями:
  `name`, `price`, `sizes`, `description`, `image` (опционально).
- Валидация: название непустое (≤160 символов), цена &gt; 0 (поддерживает
  разделители `.` и `,`), фото — JPEG/PNG/WebP/GIF до 5 МБ.
- Файлы сохраняются в `backend/uploads/` и раздаются по `/uploads/...`
  через `StaticFiles`.
- При успехе — редирект на `/seller/products`.
- Товар создаётся со статусом `pending` (на модерации).

## UC-7: модерация заявок (администратор)

- `GET /admin` — панель администратора со счётчиками статусов.
- `GET /admin/products?status=pending|published|rejected|all` — список
  заявок с фильтром по статусу (по умолчанию `pending`).
- `GET /admin/products/{id}` — карточка заявки: фото, цена, размеры,
  описание, продавец, действия модерации.
- `POST /admin/products/{id}/approve` — переводит заявку в `published`,
  очищает причину отказа. Доступно только для заявок в статусе `pending`
  (иначе 409).
- `POST /admin/products/{id}/reject` — `application/x-www-form-urlencoded`
  с полем `reason` (обязательное, ≤500 символов). Переводит в `rejected`
  и сохраняет причину. Также 409 если заявка уже не в `pending`.
- После любого действия — редирект на `/admin/products?status=pending`.
- Продавец видит причину отказа в `/seller/products`.

## Использование PostgreSQL (опционально)

Если хотите следовать ТЗ дословно (PostgreSQL):

1. Поднимите PostgreSQL и создайте БД, например `clothing_sales`.
2. В `.env` пропишите:

   ```
   DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/clothing_sales
   ```

3. Перезапустите сервер. Таблицы создадутся автоматически.

Самый быстрый способ поднять Postgres локально:

```bash
docker run --name clothing-pg -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=clothing_sales -p 5432:5432 -d postgres:16
```

## Стек

- FastAPI + Uvicorn — веб-сервер и роутинг
- Jinja2 — серверный рендеринг HTML
- SQLAlchemy 2.0 — ORM (SQLite/PostgreSQL)
- passlib + bcrypt — хеширование паролей
- Starlette SessionMiddleware + itsdangerous — сессии в cookie
- Pydantic / pydantic-settings — настройки
