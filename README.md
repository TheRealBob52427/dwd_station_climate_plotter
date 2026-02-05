# DWD Station Climate Plotter 🌦️

A Flask-based web application that visualizes historical climate data from the German Meteorological Service (DWD). It allows users to select specific weather stations and view recent weather trends, including temperature, precipitation, and sunshine duration.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

## Features

* **Data Retrieval:** Fetches daily climate data directly from the DWD OpenData server (Recent archive).
* **Dynamic Visualization:** Generates plots for temperature, rainfall, and sunshine duration using Matplotlib.
* **Station Selection:** Users can switch between pre-configured weather stations via a dropdown menu.
* **Auto-Deployment:** Includes a webhook mechanism for automatic updates from GitHub to PythonAnywhere (Free Tier compatible).
* **Modular Design:** Clean separation of concerns (logic, plotting, configuration, routes).

## Project Structure

```text
dwd_station_climate_plotter/
├── config.py            # Configuration (Stations, Secrets, Paths)
├── weather_logic.py     # Data fetching and CSV parsing logic
├── plotting.py          # Matplotlib diagram generation
├── flask_app.py         # Main Flask application & Webhook entry point
├── templates/           # HTML Templates
│   └── index.html       # Main dashboard template
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Setup for PythonAnywhere
* my PythonAnywhere profile is here: https://www.pythonanywhere.com/user/bbruns/
* add library path path "/home/bbruns/mysite/dwd_station_climate_plotter" to pulled repo code in "/var/www/bbruns_pythonanywhere_com_wsgi.py"
* open bash console: https://github.com/TheRealBob52427/dwd_station_climate_plotter.git && pip install --user -r ~/mysite/dwd_station_climate_plotter/requirements.txt

# Note
* Check that secret in config.py matches secret specified via "token" variable in Webhook: https://github.com/TheRealBob52427/dwd_station_climate_plotter/settings/hooks/594854373

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details. Data is provided by Deutscher Wetterdienst ([DWD](https://www.dwd.de/DE/Home/home_node.html)) and is licensed under [GeoNutzV](https://www.dwd.de/DE/service/copyright/copyright_node.html)
