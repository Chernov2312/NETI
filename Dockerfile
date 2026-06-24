FROM python:3.13-slim

LABEL maintainer="Max"
LABEL description="Каталог проектов NETI"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && apt-get install -y bash

COPY requirements ./requirements

RUN pip install --no-cache-dir -r requirements/prod.txt
COPY . .
CMD ["python", "neti/manage.py", "runserver", "0.0.0.0:8000"]