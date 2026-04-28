FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install deps in a separate layer for better caching.
# A stub app/ package is created so hatchling can resolve the project
# without needing the full source tree at this stage.
COPY pyproject.toml .
RUN mkdir -p app && touch app/__init__.py && \
    pip install --no-cache-dir .

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "sh scripts/prestart.sh && fastapi run app/main.py"]
