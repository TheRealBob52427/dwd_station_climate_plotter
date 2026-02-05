"""
Main application for the DWD Station Climate Plotter.
Handles web requests, renders templates, and manages GitHub webhooks for auto-deployment.
"""
import os
from datetime import datetime

from flask import Flask, render_template, request, jsonify
import git

import config
from weather_logic import get_weather_data
from plotting import create_plot

app = Flask(__name__)

def get_git_hash():
    """
    Retrieves the short Git commit hash of the current version.
    Returns 'unknown' if the repository cannot be accessed.
    """
    try:
        # Path to the current directory
        repo_path = os.path.dirname(os.path.abspath(__file__))
        repo = git.Repo(repo_path)
        # Return the first 7 characters of the hash (e.g., a1b2c3d)
        return repo.head.object.hexsha[:7]
    except Exception: # pylint: disable=broad-exception-caught
        return "unknown"

# Calculate Git hash once at startup (Global Scope)
CURRENT_GIT_HASH = get_git_hash()

# --- MAIN ROUTE ---
@app.route('/')
def index():
    """
    Main dashboard: Fetches weather data based on parameters and renders the UI.
    """
    # 1. Get Station ID from URL parameter
    station_id = request.args.get('station_id', '02667')
    if station_id not in config.STATIONS:
        station_id = "02667"
    station_name = config.STATIONS[station_id]

    # 2. Get Time Range (days) from URL parameter
    try:
        days_back = int(request.args.get('days', config.DEFAULT_DAYS))
        # Validation: Only allow defined time ranges
        if days_back not in config.TIME_RANGES:
            days_back = config.DEFAULT_DAYS
    except ValueError:
        days_back = config.DEFAULT_DAYS

    # 3. Fetch data for the dynamic time range
    data_rows, summary_or_error = get_weather_data(days_back=days_back, station_id=station_id)

    # Generate UTC timestamp for client-side local time conversion (ISO 8601)
    current_time_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    plot_json = None
    if data_rows:
        plot_json = create_plot(data_rows)

    return render_template(
        'index.html',
        rows=data_rows,
        summary=summary_or_error,
        error=summary_or_error if data_rows is None else None,
        plot_json=plot_json,  # Changed from plot_url

        # Pass configuration to template
        stations=config.STATIONS,
        current_station=station_id,
        station_name=station_name,

        # Pass time selection data
        time_ranges=config.TIME_RANGES,
        current_days=days_back,

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

    # Security check
    if token != config.WEBHOOK_SECRET:
        return jsonify({"message": "Forbidden", "error": "Invalid token"}), 403

    try:
        # Initialize Repo object for the current directory
        repo = git.Repo(os.path.dirname(os.path.abspath(__file__)))
        origin = repo.remotes.origin
        
        # Pull latest changes from GitHub
        pull_info = origin.pull()

        # Touch the WSGI file to force a reload on PythonAnywhere
        if os.path.exists(config.WSGI_FILE_PATH):
            os.utime(config.WSGI_FILE_PATH, None)
            return jsonify({
                "message": "Updated successfully",
                "git_info": str(pull_info)
            }), 200

        # Refactored to avoid unnecessary 'else' (Pylint R1705)
        return jsonify({
            "message": "Git pull successful, but WSGI file not found for reload.",
            "path_checked": config.WSGI_FILE_PATH
        }), 200

    except Exception as exc: # pylint: disable=broad-exception-caught
        return jsonify({"message": "Error during update", "error": str(exc)}), 500
