#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting build process..."

# Install Python dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Navigate to Django project directory
cd factory_erp

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Run migrations
echo "Running database migrations..."
python manage.py migrate --no-input

# Create management commands groups
echo "Setting up user groups..."
python manage.py create_master_group || echo "Master group already exists"
python manage.py create_lohia_groups || echo "Lohia groups already exist"

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'changeme123')
    print('✅ Superuser created: admin / changeme123')
else:
    print('ℹ️  Superuser already exists')
END

echo "✅ Build completed successfully!"

