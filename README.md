# Safetrace Backend

Safetrace Backend is a Django-based API backend for supply chain traceability, with a case study implementation for a cooperative in Sekadau Regency, West Kalimantan.

## Dependencies
- Python 3.12
- GDAL library (for shapefile processing)
- Poppler (for pdf2image)
- PostgreSQL with PostGIS extension
- Redis (for task queue)
- Ubuntu 24.04

## WHISP Integration
Safetrace uses WHISP (OpenForis WHISP) for remote sensing analysis features related to land and forest monitoring. This integration is intended to obtain risk values from the analysis results produced by the WHISP system. These analyses are processed through a dedicated Redis queue named `whisp`.

Before using features that depend on WHISP, make sure the following values are available in the `.env` file:
```bash
WHISP_API_URL=https://whisp.openforis.org/api
WHISP_API_KEY=your-whisp-api-key
```

If the WHISP API key is not configured, features that rely on this service will not work properly. In local development, the backend can still run, but the parts dependent on WHISP will fail or return no analysis results.

## GEE Service Account Credentials
Several features in this project rely on Google Earth Engine (GEE) access through a Google service account. To make these features work correctly, the GEE service account must be configured with the appropriate credentials and access permissions.

In the Django settings, the following configuration values are required:
- `GEE_SERVICE_ACCOUNT_EMAIL`: the Google service account email address used by the project
- `GEE_SERVICE_ACCOUNT_KEY_PATH`: the file path to the service account JSON key used for authentication

These values are read in the project settings and must point to a valid service account credential file. The JSON key file should be placed in the project directory or another accessible location, and the path must be correctly set in the environment configuration.

The service account used by this project expects read access to the GEE repository managed by this project. Without that access, management commands related to GEE data retrieval may fail or return incomplete results.

If the GEE account needs access to the repository, please contact us so the account can be granted the required repository access and the management commands can run properly.

## System Dependencies (Ubuntu)

**Ubuntu 24.04 (Python 3.12):**
```bash
sudo apt update
sudo apt install -y python3-dev python3.12-dev
sudo apt install -y gdal-bin libgdal-dev
sudo apt install -y poppler-utils
sudo apt install -y postgresql postgresql-contrib postgis
sudo apt install -y redis-server
```

## Django Setup

1. **Clone repository**
    ```bash
    git clone <repository-url>
    cd safetrace
    ```

2. **Buat virtual environment**
    ```bash
    python3.12 -m venv venv
    source venv/bin/activate  # For Ubuntu
    ```

3. **Install GDAL Python bindings (matching system library version)**
    ```bash
    # Check GDAL system library version
    gdal-config --version
    
    # Install Python bindings with the same version
    pip install gdal==$(gdal-config --version)
    ```

4. **Install remaining dependencies**
    ```bash
    pip install -r requirements.txt
    ```

5. **Run database migrations**
    ```bash
    python manage.py migrate
    ```

6. **Import Indonesia administrative base data**
    After the database tables have been created, import administrative area data used by `django-wilayah-indonesia`:
    ```bash
    python manage.py import_base_csv
    ```

7. **Run the server**
    ```bash
    python manage.py runserver
    ```

8. **Access the application**
    Open your browser and visit `http://localhost:8000`

## Use Production Environment
Run:
```
export DJANGO_ENV=prod
```
This ensures the config from `settings/prod.py` is used.
Also make sure the production `.env` file is present.

## Django Production Setup
1. **Clone the project on the server (recommended in `/var/www/html`)**
    ```bash
    cd /var/www/html
    sudo git clone <repository-url> safetrace-backend
    cd safetrace-backend
    ```

2. **Prepare production environment file**
    Make sure the production `.env` file is available in the project root.

3. **Run the initial deployment script**
    ```bash
    sudo bash scripts/deploy_init.sh
    ```

4. **Validate services after deployment**
    ```bash
    sudo systemctl status safetrace
    sudo systemctl status nginx
    ```

5. **Set up cron for GEE deforestation data sync**
    Edit the crontab for the user running the app (usually `www-data` or your deploy user):
    ```bash
    sudo crontab -e
    ```

    Add the following job (example: run daily at 02:00):
    ```bash
    0 2 * * * cd /var/www/html/safetrace-backend && DJANGO_ENV=prod /var/www/html/safetrace-backend/venv/bin/python manage.py get_data_gee_deforestation >> /var/log/safetrace_gee_deforestation.log 2>&1
    ```

6. **For subsequent release updates**
    ```bash
    sudo bash scripts/deploy_update.sh
    ```

## Troubleshooting

### GDAL Installation Issues

**Error: "Python bindings of GDAL X.X.X require at least libgdal X.X.X"**

This happens because the GDAL Python bindings version does not match the system library version. Solution:

1. **Check GDAL system library version:**
   ```bash
   gdal-config --version
   ```

2. **Install GDAL Python with the same version:**
   ```bash
   pip install gdal==$(gdal-config --version)
   ```

**GDAL version note per environment:**
- **Server Ubuntu 24.04:** GDAL 3.8.4+

**Error: "Python.h: No such file or directory"**

Install Python development headers:
```bash
# Ubuntu 24.04
sudo apt install python3-dev python3.12-dev
```

### Deployment

Use the provided scripts for deployment:

**Initial deployment:**
```bash
sudo bash scripts/deploy_init.sh
```

**Update deployment:**
```bash
sudo bash scripts/deploy_update.sh
```

These scripts automatically install GDAL based on the system library version.
    


