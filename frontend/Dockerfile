# syntax=docker/dockerfile:1.6

# ---------- builder ----------
FROM node:20-alpine AS builder

WORKDIR /app

# Сначала зависимости — даёт кеш-слой при изменении только src/
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund

COPY . .
RUN npm run build

# ---------- runtime ----------
FROM nginx:1.27-alpine AS runtime

# nginx-конфиг: SPA-fallback на index.html + прокси /api, /uploads, /receipts на backend
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Собранный SPA
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1/healthz >/dev/null 2>&1 || exit 1
