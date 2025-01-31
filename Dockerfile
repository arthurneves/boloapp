FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    pkg-config \
    build-essential \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Make the entrypoint script executable
COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY docker-entrypoint.dev.sh /docker-entrypoint.dev.sh
RUN chmod +x /docker-entrypoint.sh /docker-entrypoint.dev.sh

# Copy the rest of the application
COPY . .

# Create directory for profile photos
RUN mkdir -p app/static/uploads/profile_photos

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
