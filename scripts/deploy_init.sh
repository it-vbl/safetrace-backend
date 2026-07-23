#!/bin/bash

# Variabel
BASE_DIR="/var/www/html"
PROJECT_DIR="$BASE_DIR/safetrace-backend"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="safetrace_gunicorn"
SERVICE_RQ="rq_gunicorn"
BRANCH="main"

echo "Starting deployment process..."

# Install system dependencies
echo "Installing system dependencies..."
apt update
apt install -y python3-dev gdal-bin libgdal-dev

# Masuk ke direktori project
cd $PROJECT_DIR

# Aktifkan virtual environment
source $VENV_DIR/bin/activate

# Pull kode terbaru
echo "Pulling latest code from $BRANCH..."
git pull origin $BRANCH

# Install GDAL sesuai versi system library
echo "Installing GDAL Python bindings..."
GDAL_VERSION=$(gdal-config --version)
$VENV_DIR/bin/pip install gdal==$GDAL_VERSION

# Install/update dependencies
echo "Installing dependencies..."
$VENV_DIR/bin/pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
$VENV_DIR/bin/python manage.py collectstatic --noinput

# Jalankan migrasi database
echo "Running database migrations..."
$VENV_DIR/bin/python manage.py migrate

# Copy file service ke systemd
echo "Copying service file..."
cp scripts/safetrace_gunicorn.service /etc/systemd/system/
cp scripts/rq_gunicorn.service /etc/systemd/system/

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable service (agar auto start saat boot)
echo "Enabling $SERVICE_NAME service..."
systemctl enable $SERVICE_NAME
systemctl enable $SERVICE_RQ

# Restart gunicorn service
echo "Restarting Gunicorn service..."
systemctl start $SERVICE_NAME
systemctl restart $SERVICE_RQ

# Restart Nginx
# echo "Restarting Nginx..."
systemctl restart nginx

echo "Deployment completed successfully!"