FROM python:3.12-slim

# Set environment variables to prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies if needed, then install python requests library
RUN pip install --no-cache-dir requests

# Create images directory for downloaded Feishu images
RUN mkdir -p /app/images

# Copy only the necessary python files
COPY sync_to_dify.py main.py ./

# Run the scheduler
CMD ["python", "main.py"]
