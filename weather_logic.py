"""
Logic module for the DWD Station Climate Plotter.
Responsible for downloading, unzipping, and parsing data from the DWD OpenData server.
"""
import csv
import io
import zipfile
from datetime import datetime, timedelta

import requests
from config import DWD_URL, STATION_COORDS

def _get_float_val(row, key):
    try:
        val = float(row.get(key, -999))
        return val if val > -900 else None
    except (ValueError, TypeError):
        return None

def _find_dwd_filename(response_text, station_id):
    search_pattern = f"_{station_id}_akt.zip"
    for line in response_text.splitlines():
        if search_pattern in line and "href" in line:
            start = line.find('href="') + 6
            end = line.find('">', start)
            potential = line[start:end]
            if search_pattern in potential:
                return potential
    return None

def get_forecast_data(station_id, days_ahead=7):
    """
    Fetches forecast from Open-Meteo (using DWD ICON model).
    """
    if station_id not in STATION_COORDS:
        return []
        
    lat, lon = STATION_COORDS[station_id]
    
    # Ensure we request enough days from API (max usually 14-16 for free tier)
    days_to_req = max(days_ahead, 1)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "sunshine_duration", "wind_speed_10m_max"],
        "timezone": "Europe/Berlin",
        "models": "icon_d2",  # or 'best_match' if icon_d2 is too short range for 14 days (icon_d2 is usually 48h, might fallback)
        "forecast_days": days_to_req
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        daily = data.get("daily", {})
        times = daily.get("time", [])
        
        forecast_rows = []
        for i, date_str in enumerate(times):
            # Stop if we have enough days (API might return more)
            if i >= days_ahead:
                break

            t_max = daily["temperature_2m_max"][i]
            t_min = daily["temperature_2m_min"][i]
            t_avg = (t_max + t_min) / 2 if t_max is not None and t_min is not None else None
            
            sun_sec = daily["sunshine_duration"][i]
            sun_hours = sun_sec / 3600 if sun_sec is not None else 0
            
            wind = daily.get("wind_speed_10m_max", [None])[i]

            forecast_rows.append({
                "date": datetime.strptime(date_str, "%Y-%m-%d").strftime('%d.%m.%Y'),
                "date_obj": datetime.strptime(date_str, "%Y-%m-%d"),
                "temp": t_avg,
                "rain": daily["precipitation_sum"][i],
                "sun": sun_hours,
                "wind": wind,
                # Formatted for display
                "temp_fmt": f"{t_avg:.1f}" if t_avg is not None else "-",
                "rain_fmt": f"{daily['precipitation_sum'][i]:.1f}" if daily["precipitation_sum"][i] is not None else "-",
                "sun_fmt": f"{sun_hours:.2f}" if sun_hours is not None else "-",
                "wind_fmt": f"{wind:.1f}" if wind is not None else "-",
                "type": "forecast"
            })
            
        return forecast_rows

    except Exception as e:
        print(f"Forecast Error: {e}")
        return []

def get_weather_data(days_back=30, station_id="02667"):
    # ... (Keep your existing get_weather_data function EXACTLY as it was) ...
    """
    Fetches weather data from the DWD OpenData server...
    (Paste the content of your original get_weather_data here)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    rows = []
    summary = {"avg_temp": 0, "sum_rain": 0, "sum_sun": 0}
    temps = []

    try:
        response = requests.get(DWD_URL, timeout=10)
        file_name = _find_dwd_filename(response.text, station_id)
        if not file_name:
            return None, f"File for station {station_id} not found on server."

        zip_resp = requests.get(DWD_URL + file_name, timeout=30)
        with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as z_file:
            data_filename = [n for n in z_file.namelist() if n.startswith("produkt_")][0]
            with z_file.open(data_filename) as f_obj:
                content = f_obj.read().decode('utf-8')
                reader = csv.DictReader(content.splitlines(), delimiter=';')
                reader.fieldnames = [name.strip() for name in reader.fieldnames]
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
                        temp = _get_float_val(row, 'TMK')
                        rain = _get_float_val(row, 'RSK')
                        sun = _get_float_val(row, 'SDK')
                        wind = _get_float_val(row, 'FX')
                        rows.append({
                            "date": date_obj.strftime('%d.%m.%Y'),
                            "date_obj": date_obj,
                            "temp": temp,
                            "rain": rain,
                            "sun": sun,
                            "wind": wind,
                            "temp_fmt": f"{temp:.1f}" if temp is not None else "-",
                            "rain_fmt": f"{rain:.1f}" if rain is not None else "-",
                            "sun_fmt": f"{sun:.2f}" if sun is not None else "-",
                            "wind_fmt": f"{wind:.1f}" if wind is not None else "-"
                        })
                        if rain: summary["sum_rain"] += rain
                        if sun: summary["sum_sun"] += sun
                        if temp: temps.append(temp)
    except Exception as exc:
        return None, str(exc)

    if temps: summary["avg_temp"] = round(sum(temps)/len(temps), 2)
    summary["sum_rain"] = round(summary["sum_rain"], 2)
    summary["sum_sun"] = round(summary["sum_sun"], 2)
    rows.reverse()
    return rows, summary
