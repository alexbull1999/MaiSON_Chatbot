# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies and build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    libc-dev \
    linux-headers-generic \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project for installation
COPY . .
RUN pip install -e .

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY . .

# Create startup script - do this BEFORE switching to non-root user
COPY <<EOF /app/start.sh
#!/bin/bash
echo "Starting MaiSON Chatbot API..."

echo "Checking database connection..."
python -c "from app.database.db_connection import engine; engine.connect()" || { echo "Database connection failed"; exit 1; }

echo "Checking current migration state..."
alembic current

echo "Running database migrations..."
alembic upgrade head || { echo "Migration failed"; exit 1; }

echo "Verifying database tables..."
python -c "from app.database import Base, engine; print('Tables in metadata:', ', '.join(Base.metadata.tables.keys())); from sqlalchemy import inspect; inspector = inspect(engine); print('Tables in database:', ', '.join(inspector.get_table_names()))"

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips "*"
EOF

# Set permissions on startup script - do this BEFORE switching to non-root user
RUN chmod +x /app/start.sh

# Create non-root user and change ownership AFTER creating all files
RUN useradd -m appuser && chown -R appuser:appuser /app

# Switch to non-root user AFTER all file operations that require root
USER appuser

# Expose both HTTP and HTTPS ports
EXPOSE 8000 443

# Healthcheck to ensure application is running
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Command to run the application with migrations
CMD ["/app/start.sh"] 