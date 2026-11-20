FROM python:3.13-slim AS base

LABEL maintainer="Max"
LABEL description="Каталог проектов NETI"

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements ./requirements
RUN pip install --no-cache-dir -r requirements/prod.txt

FROM base AS development
RUN pip install --no-cache-dir -r requirements/dev.txt
COPY neti ./neti
CMD ["python", "neti/manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS production
COPY neti ./neti
RUN DJANGO_SECRET_KEY=collectstatic-only DJANGO_DB_ENGINE=sqlite \
    python neti/manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "--chdir", "neti", "--bind", "0.0.0.0:8000", "neti.wsgi:application"]
