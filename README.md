# DWD Station Climate Plotter & Forecast 🌦️

A Flask-based web application that visualizes **historical climate data** from the German Meteorological Service (DWD) and provides **local weather forecasts** using the Open-Meteo API (DWD ICON-D2 model).

It fetches daily observations, parses them, and renders **interactive** charts where historical data transitions seamlessly into the forecast.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Docker Image](https://img.shields.io/badge/docker-ghcr.io-blue?logo=docker&logoColor=white)](https://github.com/users/TheRealBob52427/packages/container/package/dwd_station_climate_plotter)
[![GitHub Release](https://img.shields.io/github/v/release/TheRealBob52427/dwd_station_climate_plotter?label=stable)](https://github.com/TheRealBob52427/dwd_station_climate_plotter/releases)
[![Pylint](https://github.com/TheRealBob52427/dwd_station_climate_plotter/actions/workflows/pylint.yml/badge.svg)](https://github.com/TheRealBob52427/dwd_station_climate_plotter/actions/workflows/pylint.yml)

## ✨ Features

* **Live Historical Data:** Fetches daily climate data directly from the DWD OpenData server (Recent archive).
* **High-Res Forecasts:** Integrates 3 to 14-day forecasts via [Open-Meteo](https://open-meteo.com/), utilizing DWD's high-resolution **ICON-D2** model.
* **Interactive Visualization:**
    * Uses **Plotly** to generate responsive charts.
    * Visual distinction between historical (solid) and forecast (dashed/transparent) data.
    * Combined temperature trends and precipitation/sunshine bars.
* **Customizable Views:**
    * Select specific weather stations.
    * Adjust historical time range (e.g., last 30, 90, 365 days).
    * Adjust forecast range (e.g., next 3, 7, 14 days).
* **Auto-Deployment:** Built-in webhook endpoint (`/update_server`) to trigger automatic updates from GitHub to PythonAnywhere.

## 🛠️ Tech Stack

* **Python 3.10+**
* **Flask:** Web framework.
* **Plotly:** Frontend graphing library.
* **Requests:** HTTP library for fetching data.
* **GitPython:** For handling auto-deployment operations.
* **APIs:** DWD OpenData (ZIP/CSV parsing) & Open-Meteo (JSON).

## 📂 Project Structure

```text
dwd_station_climate_plotter/
├── config.py            # Configuration (Stations, Coords, Secrets, Ranges)
├── weather_logic.py     # Data fetching: DWD (ZIP/CSV) & Open-Meteo (JSON)
├── plotting.py          # Plotly JSON chart generation (History + Forecast)
├── flask_app.py         # Main Flask application & Routes
├── templates/
│   └── index.html       # Dashboard template with Plotly.js integration
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker container configuration
└── README.md            # Documentation

```

## 🚀 Getting Started

### 1. Local Installation

To run the application on your local machine:

1. **Clone the repository:**
```bash
git clone [https://github.com/TheRealBob52427/dwd_station_climate_plotter.git](https://github.com/TheRealBob52427/dwd_station_climate_plotter.git)
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

### 2. Docker Usage

The project includes a `Dockerfile` that handles system dependencies (like `git`) automatically.

1. **Build the image:**
```bash
docker build -t dwd_weather_app .

```


2. **Run the container:**
```bash
docker run -p 5000:5000 dwd_weather_app

```


Access the app at `http://localhost:5000`.

### 3. Configuration

Open `config.py` to adjust settings:

* **Stations:** Edit `STATIONS` (names) and `STATION_COORDS` (Lat/Lon) to add new locations. *Note: Coordinates are required for the forecast feature.*
* **Time Ranges:** Modify `TIME_RANGES` (history) or `FORECAST_RANGES` (prediction) to change dropdown options.
* **Security:** Change the `WEBHOOK_SECRET` if using the auto-deploy feature.

## ☁️ Deployment on PythonAnywhere

This project is designed to run on the PythonAnywhere Free Tier.
My deployment is here: https://bbruns.pythonanywhere.com/?station_id=02667&days=30

1. **Pull the code:**
Open a Bash console on PythonAnywhere and clone your repo.
2. **Install Dependencies:**
```bash
pip install --user -r ~/dwd_station_climate_plotter/requirements.txt

```


3. **Configure WSGI:**
In the "Web" tab, edit your WSGI configuration file to point to `flask_app.py`.
```python
import sys
import os
project_home = '/home/yourusername/dwd_station_climate_plotter'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path
from flask_app import app as application

```


4. **Setup Webhook (Optional):**
Configure a GitHub Webhook pointing to `http://yourusername.pythonanywhere.com/update_server?token=YOUR_SECRET` to auto-update on push.

## 📄 License & Data Sources

* **License:** This project is licensed under the **Apache License 2.0** ([LICENSE](LICENSE)).
* **Historical Data:** Provided by the **Deutscher Wetterdienst (DWD)** via their [OpenData Server](https://opendata.dwd.de/).
* **Forecast Data:** Provided by **[Open-Meteo.com](https://open-meteo.com/)** under the [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license.

```

```
