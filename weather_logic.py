"""
Logic module for the DWD Station Climate Plotter.
Responsible for downloading, unzipping, and parsing data from the DWD OpenData server.
"""
import csv
import io
import zipfile
from datetime import datetime, timedelta

import requests
from config import DWD_URL
from config import DWD_URL, STATION_COORDS

def _get_float_val(row, key):
    """
    Helper function: Reads a value from the CSV row and converts it to float.
    Ignores DWD error values (usually -999).
    """
    try:
        val = float(row.get(key, -999))
        # DWD uses -999 for missing values
        return val if val > -900 else None
    except (ValueError, TypeError):
        return None


def _find_dwd_filename(response_text, station_id):
    """
    Searches the HTML response from the DWD server for the matching ZIP filename.
    """
    search_pattern = f"_{station_id}_akt.zip"

    for line in response_text.splitlines():
        if search_pattern in line and "href" in line:
            # Extract the filename from the href tag
            start = line.find('href="') + 6
            end = line.find('">', start)
            potential = line[start:end]
            
            if search_pattern in potential:
                return potential
    return None

def get_forecast_data(station_id):
    """
    Fetches 7-day forecast from Open-Meteo (using DWD ICON model).
    """
    if station_id not in STATION_COORDS:
        return None
        
    lat, lon = STATION_COORDS[station_id]
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "sunshine_duration"],
        "timezone": "Europe/Berlin",
        "models": "icon_d2"  # Explicitly use DWD's high-res model
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        daily = data.get("daily", {})
        times = daily.get("time", [])
        
        forecast_rows = []
        for i, date_str in enumerate(times):
            # Calculate avg temp from min/max for consistency with historical plot
            t_max = daily["temperature_2m_max"][i]
            t_min = daily["temperature_2m_min"][i]
            t_avg = (t_max + t_min) / 2 if t_max is not None and t_min is not None else None
            
            # Open-Meteo gives sunshine in seconds, convert to hours
            sun_sec = daily["sunshine_duration"][i]
            sun_hours = sun_sec / 3600 if sun_sec is not None else 0

            forecast_rows.append({
                "date": datetime.strptime(date_str, "%Y-%m-%d").strftime('%d.%m.%Y'),
                "date_obj": datetime.strptime(date_str, "%Y-%m-%d"),
                "temp": t_avg,
                "rain": daily["precipitation_sum"][i],
                "sun": sun_hours,
                "type": "forecast" # Marker to distinguish in plotting
            })
            
        return forecast_rows

    except Exception as e:
        print(f"Forecast Error: {e}")
        return []

def get_weather_data(days_back=30, station_id="02667"):
    """
    Fetches weather data from the DWD OpenData server, unzips it,
    and parses the CSV for the specified time range.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    rows = []
    summary = {"avg_temp": 0, "sum_rain": 0, "sum_sun": 0}
    temps = []

    try:
        # 1. Find filename on the server
        # Added timeout to avoid hanging indefinitely
        response = requests.get(DWD_URL, timeout=10)
        file_name = _find_dwd_filename(response.text, station_id)

        if not file_name:
            return None, f"File for station {station_id} not found on server."

        # 2. Download & Unzip
        zip_resp = requests.get(DWD_URL + file_name, timeout=30)
        with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as z_file:
            # The actual data file starts with "produkt_"
            data_filename = [n for n in z_file.namelist() if n.startswith("produkt_")][0]

            with z_file.open(data_filename) as f_obj:
                content = f_obj.read().decode('utf-8')
                reader = csv.DictReader(content.splitlines(), delimiter=';')
                # Strip whitespace from headers
                reader.fieldnames = [name.strip() for name in reader.fieldnames]

                # Determine date column name (DWD naming varies sometimes)
                if "MESS_DATUM" in reader.fieldnames:
                    date_col = "MESS_DATUM"
                else:
                    date_col = "MESS_DATUM_BEGINN"

                for row in reader:
                    try:
                        date_obj = datetime.strptime(row[date_col], "%Y%m%d")
                    except ValueError:
                        continue

                    if start_date <= date_obj <= end_date:
                        # Extract values
                        temp = _get_float_val(row, 'TMK')  # Daily mean temp
                        rain = _get_float_val(row, 'RSK')  # Precipitation
                        sun = _get_float_val(row, 'SDK')   # Sunshine duration
                        wind = _get_float_val(row, 'FX')   # Max wind gust

                        # Collect data for the table
                        rows.append({
                            "date": date_obj.strftime('%d.%m.%Y'),
                            "date_obj": date_obj,
                            "temp": temp,
                            "rain": rain,
                            "sun": sun,
                            "wind": wind,
                            # Formatted strings for display
                            "temp_fmt": f"{temp:.1f}" if temp is not None else "-",
                            "rain_fmt": f"{rain:.1f}" if rain is not None else "-",
                            "sun_fmt": f"{sun:.2f}" if sun is not None else "-",
                            "wind_fmt": f"{wind:.1f}" if wind is not None else "-"
                        })

                        # Update statistics
                        if rain:
                            summary["sum_rain"] += rain
                        if sun:
                            summary["sum_sun"] += sun
                        if temp:
                            temps.append(temp)

    except Exception as exc:  # pylint: disable=broad-exception-caught
        return None, str(exc)

    # Finalize statistics
    if temps:
        summary["avg_temp"] = round(sum(temps)/len(temps), 2)

    summary["sum_rain"] = round(summary["sum_rain"], 2)
    summary["sum_sun"] = round(summary["sum_sun"], 2)

    # Sort: Newest date first for the table
    rows.reverse()

    return rows, summary
