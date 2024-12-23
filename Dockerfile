# Dockerfile

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Установка русского языка spacy, если нужно
RUN python -m spacy download ru_core_news_md

COPY . .

# Точка входа: сразу запускаем main.py
ENTRYPOINT ["python", "main.py"]
