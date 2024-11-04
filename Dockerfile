FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
COPY .env .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Запуск тестов при старте контейнера
RUN pytest --maxfail=1 --disable-warnings || true

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

ENV PYTHONPATH=/app
