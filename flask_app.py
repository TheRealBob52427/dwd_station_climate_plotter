# flask_app.py
from flask import Flask, render_template, request, jsonify
import git
import os
import config
from datetime import datetime
from weather_logic import get_weather_data
from plotting import create_plot

app = Flask(__name__)

# --- MAIN ROUTE ---
@app.route('/')
def index():
    # Get station ID from URL, default to Köln/Bonn (02667)
    station_id = request.args.get('station_id', '02667')
    if station_id not in config.STATIONS:
        station_id = "02667"
    station_name = config.STATIONS[station_id]

    # Fetch data
    data_rows, summary_or_error = get_weather_data(days_back=30, station_id=station_id)

    # Generate current timestamp for "Last Update" display
    # Format: DD.MM.YYYY HH:MM:SS
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

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
        last_update=current_time,        # <--- PASSING TIMESTAMP
        github_url=config.GITHUB_REPO_URL # <--- PASSING REPO URL
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
