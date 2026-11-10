FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root

COPY . .

EXPOSE 8090

CMD ["fastapi", "run", "api/app.py", "--host", "0.0.0.0", "--port", "8090"]
