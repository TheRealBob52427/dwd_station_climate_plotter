"""
configuration settings for data retrieval and automatic release on pythonanywhere with github webhook
"""

# Your secret token for the GitHub Webhook.
WEBHOOK_SECRET = "MY_SUPER_SECRET_TOKEN_123"

# Path to your WSGI file on PythonAnywhere to trigger a reload.
WSGI_FILE_PATH = "/var/www/bbruns_pythonanywhere_com_wsgi.py"

# Available weather stations
STATIONS = {
    "02667": "Köln/Bonn",
    "03623": "Nörvenich-Niederbolheim",
    "15000": "Aachen-Orsbach"
}

STATION_COORDS = {
    "02667": (50.8659, 7.1427),   # Köln/Bonn
    "03623": (50.8167, 6.6500),   # Nörvenich
    "15000": (50.7983, 6.0244)    # Aachen-Orsbach
}

# Range for historical data query
TIME_RANGES = {
    30: "last 30 days",
    60: "last 60 days",
    90: "last 90 days",
    182: "last 6 months",
    365: "last year"
}

# Range for forecast data query
FORECAST_RANGES = {
    3: "next 3 days",
    7: "next 7 days",
    14: "next 14 days"
}

# Default ranges
DEFAULT_DAYS = 30
DEFAULT_FORECAST_DAYS = 7

# DWD OpenData Base URL
DWD_URL = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/recent/"

# Project Settings
GITHUB_REPO_URL = "https://github.com/TheRealBob52427/dwd_station_climate_plotter"

APP_VERSION = "1.1.0"
