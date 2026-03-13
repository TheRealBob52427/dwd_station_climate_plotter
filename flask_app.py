"""
Main application for the DWD Station Climate Plotter.
Handles web requests, renders templates, and manages GitHub webhooks for auto-deployment.
"""
import os
from datetime import datetime

from flask import Flask, render_template, request, jsonify
import git

import config
from weather_logic import get_weather_data, get_forecast_data, enrich_with_pv_data
from plotting import create_plot

app = Flask(__name__)

def get_git_hash():
    """
    Retrieves the short Git commit hash of the current version.
    Returns 'unknown' if the repository cannot be accessed.
    """
    try:
        repo_path = os.path.dirname(os.path.abspath(__file__))
        repo = git.Repo(repo_path)
        return repo.head.object.hexsha[:7]
    except Exception: # pylint: disable=broad-exception-caught
        return "unknown"

CURRENT_GIT_HASH = get_git_hash()

# --- MAIN ROUTE ---
@app.route('/')
def index():
    # 1. Station ID
    station_id = request.args.get('station_id', '02667')
    if station_id not in config.STATIONS:
        station_id = "02667"
    station_name = config.STATIONS[station_id]

    # 2. Historical Time Range
    try:
        days_back = int(request.args.get('days', config.DEFAULT_DAYS))
        if days_back not in config.TIME_RANGES:
            days_back = config.DEFAULT_DAYS
    except ValueError:
        days_back = config.DEFAULT_DAYS

    # 3. Forecast Time Range
    try:
        days_forecast = int(request.args.get('fc_days', config.DEFAULT_FORECAST_DAYS))
        if days_forecast not in config.FORECAST_RANGES:
            days_forecast = config.DEFAULT_FORECAST_DAYS
    except ValueError:
        days_forecast = config.DEFAULT_FORECAST_DAYS

    # 4. Fetch data (Weather, Forecast, and PV Yield)
    data_rows, summary_or_error = get_weather_data(days_back=days_back, station_id=station_id)
    forecast_rows = get_forecast_data(station_id, days_ahead=days_forecast)
    
    # NEU: PV-Daten in beide Listen (Historie & Forecast) injizieren
    data_rows, forecast_rows = enrich_with_pv_data(data_rows, forecast_rows)

    # 5. Generate Plot (benötigt jetzt kein drittes Argument mehr)
    plot_json = None
    if data_rows or forecast_rows:
        plot_json = create_plot(data_rows, forecast_rows)

    current_time_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    return render_template(
        'index.html',
        rows=data_rows,
        forecast_rows=forecast_rows,
        summary=summary_or_error,
        error=summary_or_error if data_rows is None else None,
        plot_json=plot_json,

        # Config
        stations=config.STATIONS,
        current_station=station_id,
        station_name=station_name,

        # Selectors
        time_ranges=config.TIME_RANGES,
        current_days=days_back,
        forecast_ranges=config.FORECAST_RANGES,
        current_fc_days=days_forecast,

        # Metadata
        last_update=current_time_iso,
        github_url=config.GITHUB_REPO_URL,
        app_version=config.APP_VERSION,
        git_hash=CURRENT_GIT_HASH
    )

# --- WEBHOOK FOR GITHUB AUTO-DEPLOY ---
@app.route('/update_server', methods=['POST'])
def webhook():
    """
    Receives the GitHub Webhook, pulls the latest code, and triggers a server reload.
    """
    token = request.args.get('token')

    if token != config.WEBHOOK_SECRET:
        return jsonify({"message": "Forbidden", "error": "Invalid token"}), 403

    try:
        repo = git.Repo(os.path.dirname(os.path.abspath(__file__)))
        origin = repo.remotes.origin
        pull_info = origin.pull()

        if os.path.exists(config.WSGI_FILE_PATH):
            os.utime(config.WSGI_FILE_PATH, None)
            return jsonify({
                "message": "Updated successfully",
                "git_info": str(pull_info)
            }), 200

        return jsonify({
            "message": "Git pull successful, but WSGI file not found for reload.",
            "path_checked": config.WSGI_FILE_PATH
        }), 200

    except Exception as exc: # pylint: disable=broad-exception-caught
        return jsonify({"message": "Error during update", "error": str(exc)}), 500