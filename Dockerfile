# ---- БАЗОВЫЙ ОБРАЗ ----------------------------------------------------------
FROM python:3.12-slim-trixie



# ---- НАСТРОЙКА ОКРУЖЕНИЯ ----------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    # Порт вашего FastAPI-сервиса внутри контейнера
    APP_PORT=8000

# По желанию можно добавить системные утилиты (например, для отладки сети):
# RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping curl && rm -rf /var/lib/apt/lists/*

# ---- УСТАНОВКА ЗАВИСИМОСТЕЙ (pyproject + uv.lock через uv) ---------------------
# Установим curl для инсталляции uv и сразу поставим uv
# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Копируем файлы проекта, влияющие на зависимости, отдельно для кеширования слоя
WORKDIR /app
COPY pyproject.toml uv.lock ./

# Синхронизируем окружение через uv (создаст .venv в /app)
RUN /root/.local/bin/uv sync --frozen --no-dev --no-editable

# Используем виртуальное окружение проекта по умолчанию
ENV PATH="/app/.venv/bin:${PATH}"

# ---- КОПИРУЕМ ПРОЕКТ ---------------------------------------------------------
COPY . .

# ---- ENTRYPOINT --------------------------------------------------------------
# Сценарий старта: ждём БД -> alembic upgrade head -> uvicorn
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ---- СЕТЬ/ПОРТ ---------------------------------------------------------------
EXPOSE ${APP_PORT}

# ---- КОМАНДА ПО УМОЛЧАНИЮ ----------------------------------------------------
CMD ["/entrypoint.sh"]