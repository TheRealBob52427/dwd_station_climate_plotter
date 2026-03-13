"""
Logic module for the DWD Station Climate Plotter.
Responsible for downloading, unzipping, and parsing data from the DWD OpenData server,
fetching forecasts, and generating PV yield predictions via Linear Regression.
"""
import csv
import io
import zipfile
from datetime import datetime, timedelta

import requests
import pandas as pd
from sklearn.linear_model import LinearRegression

import config

def _get_float_val(row, key):
    """Helper to safely extract float values from CSV rows."""
    try:
        val = float(row.get(key, -999))
        return val if val > -900 else None
    except (ValueError, TypeError):
        return None

def _find_dwd_filename(response_text, station_id):
    """Parses the DWD directory HTML to find the correct zip file for a station."""
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
    """Fetches weather forecast from Open-Meteo API using the DWD ICON model."""
    if station_id not in config.STATION_COORDS:
        return []
        
    lat, lon = config.STATION_COORDS[station_id]
    days_to_request = max(days_ahead, 1)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "sunshine_duration", "wind_speed_10m_max"],
        "timezone": "Europe/Berlin",
        "models": "icon_d2",
        "forecast_days": days_to_request
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        daily = data.get("daily", {})
        times = daily.get("time", [])
        
        forecast_rows = []
        for i, date_str in enumerate(times):
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
                "temp_fmt": f"{t_avg:.1f}" if t_avg is not None else "-",
                "rain_fmt": f"{daily['precipitation_sum'][i]:.1f}" if daily["precipitation_sum"][i] is not None else "-",
                "sun_fmt": f"{sun_hours:.2f}" if sun_hours is not None else "-",
                "wind_fmt": f"{wind:.1f}" if wind is not None else "-",
                "type": "forecast"
            })
        return forecast_rows
    except Exception as exc:
        print(f"Forecast Error: {exc}")
        return []

def get_weather_data(days_back=30, station_id="02667"):
    """Fetches historical weather data from the DWD OpenData server."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    rows = []
    summary = {"avg_temp": 0, "sum_rain": 0, "sum_sun": 0}
    temps = []

    try:
        response = requests.get(config.DWD_URL, timeout=10)
        file_name = _find_dwd_filename(response.text, station_id)
        if not file_name:
            return None, f"File for station {station_id} not found on server."

        zip_resp = requests.get(config.DWD_URL + file_name, timeout=30)
        with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as z_file:
            data_filename = [n for n in z_file.namelist() if n.startswith("produkt_")][0]
            with z_file.open(data_filename) as f_obj:
                content = f_obj.read().decode('utf-8')
                reader = csv.DictReader(content.splitlines(), delimiter=';')
                reader.fieldnames = [name.strip() for name in reader.fieldnames]
                
                date_col = "MESS_DATUM" if "MESS_DATUM" in reader.fieldnames else "MESS_DATUM_BEGINN"

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

# Stelle sicher, dass pd und LinearRegression importiert sind (oben in der Datei):
# import pandas as pd
# from sklearn.linear_model import LinearRegression

def enrich_with_pv_data(historical_rows, forecast_rows):
    """
    Fetches PV data, trains the linear regression model, and enriches both 
    historical and forecast rows with 'pv_actual' and 'pv_predicted' values.
    """
    if not historical_rows and not forecast_rows:
        return historical_rows, forecast_rows

    try:
        import config  # Falls noch nicht global importiert
        import pandas as pd
        from sklearn.linear_model import LinearRegression
        
        # --- FIX: Standard-Dezimalzeichen (.) wird automatisch von Pandas erkannt ---
        df = pd.read_csv(config.PV_DATA_URL) 
        df['Tag'] = pd.to_datetime(df['Tag'], format='%d.%m.%Y', errors='coerce')
        
        features = ['TagImJahr', 'Temperatur (°C)', 'Niederschlag (mm)', 'Sonnenstunden (h)']
        target = 'PV-Ertrag (kWh)'
        
        # --- FIX: Einfache Konvertierung zu numerischen Werten ---
        for col in features + [target]:
            if col in df.columns:
                # Fehlerhafte Werte (Texte/Leerzeilen) werden zu NaN (Not a Number)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Train the model
        cutoff_train_date = pd.Timestamp(datetime.now() - timedelta(days=config.PV_TRAINING_DAYS))
        train_df = df.dropna(subset=features + [target])
        train_df = train_df[train_df['Tag'] >= cutoff_train_date]
        
        model = None
        if not train_df.empty:
            x_train = train_df[features]
            y_train = train_df[target]
            model = LinearRegression()
            model.fit(x_train, y_train)

        # Dictionary for fast lookup of actual PV data by date
        actual_pv_dict = df.dropna(subset=[target]).set_index('Tag')[target].to_dict()

        # Helper to predict PV for a single row
        def predict_for_row(row_data):
            if model is None or row_data.get('temp') is None:
                return None
            day_of_year = row_data['date_obj'].timetuple().tm_yday
            rain = row_data.get('rain') or 0.0
            sun = row_data.get('sun') or 0.0
            
            pred_df = pd.DataFrame([[day_of_year, row_data['temp'], rain, sun]], columns=features)
            pred_val = model.predict(pred_df)[0]
            return max(0.0, float(pred_val)) # Stelle sicher, dass es ein Float ist

        # Helper for safe string formatting
        def format_val(val):
            if val is None or pd.isna(val):
                return "-"
            return f"{float(val):.2f}"

        # Enrich Historical Rows
        if historical_rows:
            for row in historical_rows:
                date_ts = pd.Timestamp(row['date_obj'])
                actual = actual_pv_dict.get(date_ts, None)
                predicted = predict_for_row(row)

                # Speichere saubere Zahlen oder None
                row['pv_actual'] = float(actual) if actual is not None and not pd.isna(actual) else None
                row['pv_predicted'] = predicted
                
                # Speichere formatierte Strings für die HTML Tabelle
                row['pv_actual_fmt'] = format_val(row['pv_actual'])
                row['pv_predicted_fmt'] = format_val(row['pv_predicted'])

        # Enrich Forecast Rows
        if forecast_rows:
            for row in forecast_rows:
                predicted = predict_for_row(row)
                
                row['pv_actual'] = None # Forecast has no actual PV yield yet
                row['pv_predicted'] = predicted
                row['pv_actual_fmt'] = "-"
                row['pv_predicted_fmt'] = format_val(predicted)

    except Exception as exc:
        print(f"PV Enrichment Error: {exc}")
        # Fallback to empty values if Google Sheet fails
        for r in (historical_rows or []) + (forecast_rows or []):
            r['pv_actual'] = r['pv_predicted'] = None
            r['pv_actual_fmt'] = r['pv_predicted_fmt'] = "-"

    return historical_rows, forecast_rows
