# config.py

# Your secret token for the GitHub Webhook.
# IMPORTANT: Change this to a random secure string!
WEBHOOK_SECRET = "MY_SUPER_SECRET_TOKEN_123"

# Path to your WSGI file on PythonAnywhere to trigger a reload.
# Replace 'yourusername' with your actual PythonAnywhere username.
WSGI_FILE_PATH = "/var/www/bbruns_pythonanywhere_com_wsgi.py"

# Available weather stations
STATIONS = {
    "02667": "Köln/Bonn",
    "03623": "Nörvenich-Niederbolheim",
    "15000": "Aachen-Orsbach"
}

# range for data query
TIME_RANGES = {
    30: "last 30 days",
    60: "last 60 days",
    90: "last 90 days",
    182: "last 6 months",
    365: "last year"
}

# default range
DEFAULT_DAYS = 30

# DWD OpenData Base URL
DWD_URL = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/recent/"

# Project Settings
GITHUB_REPO_URL = "https://github.com/TheRealBob52427/dwd_station_climate_plotter"

APP_VERSION = "1.0.0"
