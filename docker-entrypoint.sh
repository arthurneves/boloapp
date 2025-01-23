#!/bin/sh

# Wait for MySQL to be ready
echo "Waiting for MySQL to be ready..."
while ! nc -z db 3306; do
  sleep 1
done
echo "MySQL is ready!"

# Initialize the database
python -c "from config.database import create_database; create_database()"

# Start Gunicorn
exec gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 "run:app"
