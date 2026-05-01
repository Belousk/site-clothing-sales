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
- Заглушки личных кабинетов для каждой роли с переходами по ролям.
- Базовая структура моделей, БД и миграций (`init_db` создаёт таблицы при старте).

Дальнейшие модули (каталог товаров, корзина, заказы, оплата, модерация заявок)
будут реализованы в следующих итерациях согласно UC-1 … UC-7 из ТЗ.

## Структура

```
backend/
├── app/
│   ├── main.py            # FastAPI приложение
│   ├── config.py          # Настройки (pydantic-settings)
│   ├── database.py        # Engine + SessionLocal + init_db
│   ├── models.py          # User, UserRole
│   ├── security.py        # passlib/bcrypt
│   ├── dependencies.py    # get_current_user
│   ├── templating.py      # Jinja2Templates
│   ├── routers/
│   │   ├── pages.py       # /, /account, /seller, /admin
│   │   └── auth.py        # /register, /login, /logout
│   ├── templates/         # base, index, login, register, buyer/seller/admin
│   └── static/styles.css  # Премиум-минимал стили
├── scripts/create_admin.py
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
   — попадёте на `/seller`.
3. Создайте администратора через `scripts/create_admin.py` и войдите
   на `/login` — попадёте на `/admin`.

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
