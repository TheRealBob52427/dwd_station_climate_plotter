"""
Plotting module for the DWD Station Climate Plotter.
Generates interactive Plotly charts for weather data visualization.
"""
import json
import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots

def create_plot(rows):
    """
    Creates an interactive Plotly chart from the provided weather rows 
    and returns it as a JSON string.
    """
    if not rows:
        return None

    # Prepare data (Reverse order: Old -> New for time axis)
    plot_data = rows[::-1]

    # Extract data columns
    # specific format YYYY-MM-DD is often better parsed by JS, 
    # but the existing date_obj is robust.
    dates = [r['date_obj'] for r in plot_data]
    temps = [r['temp'] if r['temp'] is not None else 0 for r in plot_data]
    rains = [r['rain'] if r['rain'] is not None else 0 for r in plot_data]
    suns = [r['sun'] if r['sun'] is not None else 0 for r in plot_data]

    # Create Subplots with shared X-axis
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Temperature Trend", "Rain & Sun")
    )

    # 1. Plot: Temperature (Bar)
    fig.add_trace(
        go.Bar(
            x=dates, 
            y=temps, 
            name='Temp (°C)', 
            marker_color='#d9534f',
            opacity=0.7
        ),
        row=1, col=1
    )

    # 2. Plot: Rain (Bar)
    fig.add_trace(
        go.Bar(
            x=dates, 
            y=rains, 
            name='Rain (mm)', 
            marker_color='#0275d8'
        ),
        row=2, col=1
    )

    # 3. Plot: Sun (Bar)
    fig.add_trace(
        go.Bar(
            x=dates, 
            y=suns, 
            name='Sun (h)', 
            marker_color='#f0ad4e'
        ),
        row=2, col=1
    )

    # Update Layout
    fig.update_layout(
        height=800,
        barmode='group', # Groups bars for Rain/Sun
        showlegend=True,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)', # Transparent background
        paper_bgcolor='rgba(0,0,0,0)'
    )

    # Add Grid lines manually since we made bg transparent
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#e5e5e5')
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#e5e5e5')

    # Serialize to JSON for the frontend
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
