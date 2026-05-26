# Stage 1: install dependencies
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: minimal runtime with non-root user
FROM python:3.12-slim
RUN useradd --no-create-home --shell /bin/false appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY src/ .
USER appuser
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--access-logfile", "-", "--timeout", "30", "--max-requests", "1000", "--max-requests-jitter", "100", "app:create_app()"]
