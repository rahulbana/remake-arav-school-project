# Use an official lightweight Python image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Set working directory inside the container
WORKDIR /app

# Install dependencies first (leverages Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Create a non-root user for security and grant permissions
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose the default Flask/Gunicorn port
EXPOSE 8080

# Run with Gunicorn using 4 workers bound to all interfaces
CMD ["gunicorn", "--workers=4", "--timeout=200", "--bind=0.0.0.0:8080", "app:app"]