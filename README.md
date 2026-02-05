# DWD Station Climate Plotter 🌦️

A Flask-based web application that visualizes historical climate data from the German Meteorological Service (DWD). It fetches daily observations, parses them, and renders **interactive** charts for temperature, precipitation, and sunshine duration.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Docker Image](https://img.shields.io/badge/docker-ghcr.io-blue?logo=docker&logoColor=white)](https://github.com/users/TheRealBob52427/packages/container/package/dwd_station_climate_plotter)
[![Pylint](https://github.com/TheRealBob52427/dwd_station_climate_plotter/actions/workflows/pylint.yml/badge.svg)](https://github.com/TheRealBob52427/dwd_station_climate_plotter/actions/workflows/pylint.yml)

## ✨ Features

* **Live Data Retrieval:** Fetches daily climate data directly from the DWD OpenData server (Recent archive).
* **Interactive Visualization:** Uses **Plotly** to generate responsive, interactive charts (zoom, hover actions) instead of static images.
* **Dynamic Parsing:** Handles ZIP extraction and CSV parsing of DWD data structures on the fly.
* **Customizable Views:**
* Select specific weather stations (configurable).
* Adjust time ranges (e.g., last 30, 90, 365 days).


* **Auto-Deployment:** Built-in webhook endpoint (`/update_server`) to trigger automatic updates from GitHub to PythonAnywhere.

## 🛠️ Tech Stack

* **Python 3.10+**
* **Flask:** Web framework.
* **Plotly:** Frontend graphing library.
* **Requests:** HTTP library for fetching DWD data.
* **GitPython:** For handling auto-deployment operations.

## 📂 Project Structure

```text
dwd_station_climate_plotter/
├── config.py            # Configuration (Stations, Secrets, Time ranges)
├── weather_logic.py     # Data fetching (ZIP/CSV) and parsing logic
├── plotting.py          # Plotly JSON chart generation
├── flask_app.py         # Main Flask application & Routes
├── templates/
│   └── index.html       # Dashboard template with Plotly.js integration
├── requirements.txt     # Python dependencies
└── README.md            # Documentation

```

## 🚀 Getting Started

### 1. Local Installation

To run the application on your local machine:

1. **Clone the repository:**
```bash
git clone https://github.com/TheRealBob52427/dwd_station_climate_plotter.git
cd dwd_station_climate_plotter

```


2. **Create a virtual environment (optional but recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

```


3. **Install dependencies:**
```bash
pip install -r requirements.txt

```


4. **Run the application:**
```bash
export FLASK_APP=flask_app.py
flask run

```


Open your browser at `http://127.0.0.1:5000`.

### 2. Configuration

Open `config.py` to adjust settings:

* **Stations:** Edit the `STATIONS` dictionary to add or remove DWD station IDs.


* **Security (Important):** Change the `WEBHOOK_SECRET`.
```python
# config.py
WEBHOOK_SECRET = "CHANGE_THIS_TO_A_SECURE_RANDOM_STRING"

```


## ☁️ Deployment on PythonAnywhere

This project is designed to run on the PythonAnywhere Free Tier.
My deployment is here: https://bbruns.pythonanywhere.com/?station_id=02667&days=30

1. **Pull the code:**
Open a Bash console on PythonAnywhere and clone your repo:
```bash
git clone https://github.com/YOUR_GITHUB_USER/dwd_station_climate_plotter.git

```


2. **Install Dependencies:**
```bash
pip install --user -r ~/dwd_station_climate_plotter/requirements.txt

```


3. **Configure WSGI:**
In the "Web" tab, edit your WSGI configuration file (`/var/www/yourusername_pythonanywhere_com_wsgi.py`). Add the project path:
```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/dwd_station_climate_plotter'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

from flask_app import app as application

```


4. **Setup Auto-Deployment (Webhook):**
* In `config.py`, ensure `WSGI_FILE_PATH` points to your actual WSGI file (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`).
* In your GitHub Repository Settings -> **Webhooks**:
* **Payload URL:** `http://yourusername.pythonanywhere.com/update_server?token=YOUR_SECRET_FROM_CONFIG`
* **Content type:** `application/json`
* **Events:** Just the `push` event.





## 📄 License & Data Sources

* **License:** This project is licensed under the **Apache License 2.0**.
* **Data Source:** Weather data is provided by the **Deutscher Wetterdienst (DWD)** via their [OpenData Server](https://opendata.dwd.de/).
* *Nutzungsbedingungen:* The data is available under the [GeoNutzV](https://www.dwd.de/DE/derdwd/datenpolitik.html).
