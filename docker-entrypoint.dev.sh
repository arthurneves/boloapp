#!/bin/sh

# Wait for MySQL to be ready
echo "Waiting for MySQL to be ready..."
while ! nc -z db 3306; do
  sleep 1
done
echo "MySQL is ready!"

# Initialize the database
python -c "from config.database import create_database; create_database()"

# Start Flask in development mode
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_APP=run.py
flask run --host=0.0.0.0 --port=5000