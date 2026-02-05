# weather_logic.py
import requests
import zipfile
import io
import csv
from datetime import datetime, timedelta
from config import DWD_URL

def get_weather_data(days_back=30, station_id="02667"):
    """
    Fetches weather data from DWD OpenData server, unzips it,
    and parses the CSV for the last n days.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    rows = []
    summary = {"avg_temp": 0, "sum_rain": 0, "sum_sun": 0}
    temps = []

    try:
        # 1. Find the correct filename on the server
        response = requests.get(DWD_URL)
        search_pattern = f"_{station_id}_akt.zip"
        file_name = None

        for line in response.text.splitlines():
            if search_pattern in line and "href" in line:
                start = line.find('href="') + 6
                end = line.find('">', start)
                potential = line[start:end]
                if search_pattern in potential:
                    file_name = potential
                    break

        if not file_name:
            return None, f"File for station {station_id} not found on server."

        # 2. Download and Unzip
        zip_resp = requests.get(DWD_URL + file_name)
        with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as z:
            # The data file starts with "produkt_"
            data_filename = [n for n in z.namelist() if n.startswith("produkt_")][0]
            with z.open(data_filename) as f:
                content = f.read().decode('utf-8')
                reader = csv.DictReader(content.splitlines(), delimiter=';')
                # Strip whitespace from headers
                reader.fieldnames = [name.strip() for name in reader.fieldnames]

                # Determine date column name
                date_col = "MESS_DATUM" if "MESS_DATUM" in reader.fieldnames else "MESS_DATUM_BEGINN"

                for row in reader:
                    try:
                        date_obj = datetime.strptime(row[date_col], "%Y%m%d")
                    except ValueError: continue

                    if start_date <= date_obj <= end_date:
                        def get_val(k):
                            try:
                                v = float(row.get(k, -999))
                                # DWD uses -999 for missing values
                                return v if v > -900 else None
                            except: return None

                        temp = get_val('TMK')  # Daily mean temperature
                        rain = get_val('RSK')  # Precipitation
                        sun = get_val('SDK')   # Sunshine duration
                        wind = get_val('FX')   # Max wind gust

                        # Collect data for the table
                        rows.append({
                            "date": date_obj.strftime('%d.%m.%Y'),
                            "date_obj": date_obj, # Kept for sorting in plot
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
                        if rain: summary["sum_rain"] += rain
                        if sun: summary["sum_sun"] += sun
                        if temp: temps.append(temp)

    except Exception as e:
        return None, str(e)

    # Finalize statistics
    if temps: summary["avg_temp"] = round(sum(temps)/len(temps), 2)
    summary["sum_rain"] = round(summary["sum_rain"], 2)
    summary["sum_sun"] = round(summary["sum_sun"], 2)

    # Sort: Newest date first for the table
    rows.reverse()

    return rows, summary
