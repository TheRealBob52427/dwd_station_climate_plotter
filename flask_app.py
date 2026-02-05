# flask_app.py
from flask import Flask, render_template, request, jsonify
import git
import os
import config
from datetime import datetime
from weather_logic import get_weather_data
from plotting import create_plot

app = Flask(__name__)

def get_git_hash():
    """Liest den kurzen Git-Hash des aktuellen Commits aus."""
    try:
        # Pfad zum aktuellen Ordner
        repo_path = os.path.dirname(os.path.abspath(__file__))
        repo = git.Repo(repo_path)
        # Gibt die ersten 7 Zeichen des Hashs zurück (z.B. a1b2c3d)
        return repo.head.object.hexsha[:7]
    except Exception:
        return "unknown"

# Hash einmalig beim Start berechnen (Global Scope)
CURRENT_GIT_HASH = get_git_hash()

# --- MAIN ROUTE ---
@app.route('/')
def index():
    # Get station ID from URL, default to Köln/Bonn (02667)
    station_id = request.args.get('station_id', '02667')
    if station_id not in config.STATIONS:
        station_id = "02667"
    station_name = config.STATIONS[station_id]

    try:
        days_back = int(request.args.get('days', config.DEFAULT_DAYS))
        if days_back not in config.TIME_RANGES:
            days_back = config.DEFAULT_DAYS
    except ValueError:
        days_back = config.DEFAULT_DAYS
    
    # Fetch data
    data_rows, summary_or_error = get_weather_data(days_back=days_back, station_id=station_id)

    # Generate current timestamp (UTC time in ISO format) for "Last Update" display
    current_time_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    plot_url = None
    if data_rows:
        plot_url = create_plot(data_rows)

    return render_template(
        'index.html', 
        rows=data_rows, 
        summary=summary_or_error, 
        error=summary_or_error if data_rows is None else None,
        plot_url=plot_url,
        stations=config.STATIONS,
        current_station=station_id,
        station_name=station_name,
        last_update=current_time_iso,
        github_url=config.GITHUB_REPO_URL,
        app_version=config.APP_VERSION,
        git_hash=CURRENT_GIT_HASH
    )

# --- WEBHOOK FOR GITHUB AUTO-DEPLOY ---
@app.route('/update_server', methods=['POST'])
def webhook():
    # 1. Verification
    # For simplicity, we check a URL parameter or a simple header.
    # GitHub standard webhooks send the signature in headers, but custom headers
    # are easier to configure for beginners.
    # Usage: URL in GitHub Webhook: http://user.pythonanywhere.com/update_server?token=MY_SECRET
    
    token = request.args.get('token')
    
    # Alternatively check header if you configured it that way
    # token = request.headers.get('X-Git-Token')

    if token != config.WEBHOOK_SECRET:
        return jsonify({"message": "Forbidden", "error": "Invalid token"}), 403
    
    try:
        # 2. Update Code
        # We assume this script runs inside the repo folder
        repo = git.Repo(os.path.dirname(os.path.abspath(__file__)))
        origin = repo.remotes.origin
        
        # Pull latest changes
        pull_info = origin.pull()
        
        # 3. Reload Web App
        # In PythonAnywhere Free Tier, we cannot restart the server programmatically via API.
        # But touching the WSGI file triggers a reload.
        if os.path.exists(config.WSGI_FILE_PATH):
            os.utime(config.WSGI_FILE_PATH, None)
            return jsonify({
                "message": "Updated successfully", 
                "git_info": str(pull_info)
            }), 200
        else:
            return jsonify({
                "message": "Git pull successful, but WSGI file not found for reload.",
                "path_checked": config.WSGI_FILE_PATH
            }), 200

    except Exception as e:
        return jsonify({"message": "Error during update", "error": str(e)}), 500
