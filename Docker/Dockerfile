FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app
USER botuser

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Run migrations\n\
echo "Running database migrations..."\n\
python -m alembic upgrade head || echo "Migration failed or already applied"\n\
\n\
# Seed database (optional)\n\
# python -m database.seed\n\
\n\
# Start bot\n\
echo "Starting bot..."\n\
exec python main.py\n' > /app/start.sh && chmod +x /app/start.sh

# Run application
CMD ["/app/start.sh"]
