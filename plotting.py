"""
Plotting module for the DWD Station Climate Plotter.
Generates interactive Plotly charts for weather data visualization.
"""
import json
import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots

def create_plot(historical_rows, forecast_rows=None):
    """
    Creates an interactive Plotly chart from the provided weather rows 
    (historical + optional forecast) and returns it as a JSON string.
    """
    if not historical_rows:
        return None

    # 1. Prepare Data
    # Historical data comes in Newest -> Oldest order (for the table),
    # so we reverse it for the time-series plot (Oldest -> Newest).
    hist_data = historical_rows[::-1]
    
    # Forecast data usually comes Oldest -> Newest from the API, so we keep it as is.
    fore_data = forecast_rows if forecast_rows else []

    # Helper to extract columns safely (handling None values)
    def get_cols(data):
        return (
            [r['date_obj'] for r in data],
            [r['temp'] if r['temp'] is not None else None for r in data], # Keep None for gaps if needed, or use 0
            [r['rain'] if r['rain'] is not None else 0 for r in data],
            [r['sun'] if r['sun'] is not None else 0 for r in data]
        )

    # Extract columns
    h_dates, h_temps, h_rains, h_suns = get_cols(hist_data)
    f_dates, f_temps, f_rains, f_suns = get_cols(fore_data)

    # 2. Create Subplots
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Temperature Trend (°C)", "Rain (mm) & Sun (h)")
    )

    # --- TOP PLOT: TEMPERATURE ---

    # Historical Temp (Solid Line)
    fig.add_trace(
        go.Scatter(
            x=h_dates, 
            y=h_temps, 
            name='Temp (Hist)', 
            mode='lines',
            line=dict(color='#d9534f', width=3)
        ),
        row=1, col=1
    )

    if f_dates:
        # Connect the last historical point to the first forecast point
        # This prevents a visual "gap" in the line chart
        if h_dates and h_temps[-1] is not None and f_temps[0] is not None:
            connect_x = [h_dates[-1], f_dates[0]]
            connect_y = [h_temps[-1], f_temps[0]]
            fig.add_trace(
                go.Scatter(
                    x=connect_x, y=connect_y, 
                    showlegend=False, 
                    mode='lines',
                    line=dict(color='#d9534f', dash='dot', width=2),
                    hoverinfo='skip'
                ),
                row=1, col=1
            )

        # Forecast Temp (Dotted Line)
        fig.add_trace(
            go.Scatter(
                x=f_dates, 
                y=f_temps, 
                name='Temp (Fcst)', 
                mode='lines+markers',
                line=dict(color='#d9534f', dash='dot', width=2),
                marker=dict(size=6)
            ),
            row=1, col=1
        )

    # --- BOTTOM PLOT: RAIN & SUN ---

    # Historical Rain
    fig.add_trace(
        go.Bar(
            x=h_dates, 
            y=h_rains, 
            name='Rain', 
            marker_color='#0275d8'
        ),
        row=2, col=1
    )

    # Historical Sun
    fig.add_trace(
        go.Bar(
            x=h_dates, 
            y=h_suns, 
            name='Sun', 
            marker_color='#f0ad4e'
        ),
        row=2, col=1
    )

    if f_dates:
        # Forecast Rain (Translucent)
        fig.add_trace(
            go.Bar(
                x=f_dates, 
                y=f_rains, 
                name='Rain (Fcst)', 
                marker_color='#0275d8',
                opacity=0.4,
                showlegend=False # Avoid cluttering legend
            ),
            row=2, col=1
        )

        # Forecast Sun (Translucent)
        fig.add_trace(
            go.Bar(
                x=f_dates, 
                y=f_suns, 
                name='Sun (Fcst)', 
                marker_color='#f0ad4e',
                opacity=0.4,
                showlegend=False
            ),
            row=2, col=1
        )

    # 3. Update Layout
    fig.update_layout(
        height=700,
        barmode='group', # Groups bars for Rain/Sun side-by-side
        showlegend=True,
        margin=dict(l=50, r=50, t=60, b=50),
        plot_bgcolor='rgba(0,0,0,0)', # Transparent plot area
        paper_bgcolor='rgba(0,0,0,0)', # Transparent outer area
        hovermode="x unified"          # Show all values for a specific date on hover
    )

    # Add Grid lines manually (since background is transparent)
    grid_style = dict(showgrid=True, gridwidth=1, gridcolor='#e5e5e5')
    fig.update_xaxes(**grid_style)
    fig.update_yaxes(**grid_style)

    # Visual separator for "Today" (if forecast exists)
    if f_dates:
        # Draw a vertical line at the start of the forecast
        fig.add_vline(
            x=f_dates[0], 
            line_width=1, 
            line_dash="dash", 
            line_color="gray",
            annotation_text="Forecast Start", 
            annotation_position="top left"
        )

    # Serialize to JSON for the frontend
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
