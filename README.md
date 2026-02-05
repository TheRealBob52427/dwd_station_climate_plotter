# DWD Station Climate Plotter 🌦️

A Flask-based web application that visualizes historical climate data from the German Meteorological Service (DWD). It allows users to select specific weather stations and view recent weather trends, including temperature, precipitation, and sunshine duration.

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

## License
This project is open-source. Data provided by Deutscher Wetterdienst ([DWD](https://www.dwd.de/DE/Home/home_node.html)).
