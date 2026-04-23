FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install deps in a separate layer for better caching
COPY pyproject.toml .
RUN pip install --no-cache-dir \
    "fastapi[standard]>=0.114.2" \
    "pymysql>=1.1.1" \
    "cryptography>=43.0.0" \
    "sqlmodel>=0.0.21" \
    "pydantic-settings>=2.2.1" \
    "pyjwt>=2.8.0" \
    "pwdlib[argon2,bcrypt]>=0.3.0" \
    "alembic>=1.12.1" \
    "python-multipart>=0.0.7" \
    "emails>=0.6" \
    "jinja2>=3.1.4" \
    "tenacity>=8.2.3" \
    "email-validator>=2.1.0" \
    "sentry-sdk[fastapi]>=1.40.6" \
    "httpx>=0.25.1"

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "sh scripts/prestart.sh && fastapi run app/main.py"]
