FROM python:3.12-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install required Python dependencies: requests, flask, and python-dotenv
RUN pip install --no-cache-dir requests flask python-dotenv

# Create directories for downloaded images and configuration files
RUN mkdir -p /app/images /app/config

# Copy python scripts
COPY sync_to_dify.py main.py app.py state.py ./

# Copy templates directory for Flask web frontend
COPY templates/ ./templates/

# Expose Web UI port
EXPOSE 8080

# Run the multi-threaded app/scheduler
CMD ["python", "main.py"]
