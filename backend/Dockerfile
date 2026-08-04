FROM python:3.11-slim

WORKDIR /app

# Системные зависимости, нужные для сборки psycopg/cryptography и т.д.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false

# Сначала только файлы зависимостей — для эффективного кэширования Docker-слоёв
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main

# Теперь копируем остальной код
COPY . .

COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]