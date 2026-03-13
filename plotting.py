"""
Plotting module for the DWD Station Climate Plotter.
Generates interactive Plotly charts for weather data and PV yield visualization.
"""
import json
import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots

def create_plot(historical_rows, forecast_rows=None, pv_rows=None):
    """
    Creates an interactive Plotly chart from the provided weather and PV rows 
    and returns it as a JSON string.
    """
    if not historical_rows and not pv_rows:
        return None

    # Reverse historical data for time-series plot (Oldest -> Newest)
    hist_data = historical_rows[::-1] if historical_rows else []
    fore_data = forecast_rows if forecast_rows else []

    def get_cols(data):
        return (
            [r['date_obj'] for r in data],
            [r['temp'] if r['temp'] is not None else None for r in data],
            [r['rain'] if r['rain'] is not None else 0 for r in data],
            [r['sun'] if r['sun'] is not None else 0 for r in data]
        )

    h_dates, h_temps, h_rains, h_suns = get_cols(hist_data)
    f_dates, f_temps, f_rains, f_suns = get_cols(fore_data)

    # Create 3-Row Subplots
    fig = make_subplots(
        rows=3, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("Temperature Trend (°C)", "Rain (mm) & Sun (h)", "PV Yield (kWh) - Actual vs. Predicted")
    )

    # --- TOP PLOT: TEMPERATURE ---
    if h_dates:
        fig.add_trace(
            go.Scatter(
                x=h_dates, y=h_temps, 
                name='Temp (Hist)', mode='lines',
                line=dict(color='#d9534f', width=3)
            ),
            row=1, col=1
        )

    if f_dates:
        if h_dates and h_temps[-1] is not None and f_temps[0] is not None:
            fig.add_trace(
                go.Scatter(
                    x=[h_dates[-1], f_dates[0]], y=[h_temps[-1], f_temps[0]], 
                    showlegend=False, mode='lines',
                    line=dict(color='#d9534f', dash='dot', width=2),
                    hoverinfo='skip'
                ),
                row=1, col=1
            )
        fig.add_trace(
            go.Scatter(
                x=f_dates, y=f_temps, 
                name='Temp (Fcst)', mode='lines+markers',
                line=dict(color='#d9534f', dash='dot', width=2),
                marker=dict(size=6)
            ),
            row=1, col=1
        )

    # --- MIDDLE PLOT: RAIN & SUN ---
    if h_dates:
        fig.add_trace(go.Bar(x=h_dates, y=h_rains, name='Rain', marker_color='#0275d8'), row=2, col=1)
        fig.add_trace(go.Bar(x=h_dates, y=h_suns, name='Sun', marker_color='#f0ad4e'), row=2, col=1)

    if f_dates:
        fig.add_trace(go.Bar(x=f_dates, y=f_rains, name='Rain (Fcst)', marker_color='#0275d8', opacity=0.4, showlegend=False), row=2, col=1)
        fig.add_trace(go.Bar(x=f_dates, y=f_suns, name='Sun (Fcst)', marker_color='#f0ad4e', opacity=0.4, showlegend=False), row=2, col=1)

    # --- BOTTOM PLOT: PV YIELD ---
    if pv_rows:
        p_dates = [r['date_obj'] for r in pv_rows]
        p_actual = [r['actual'] for r in pv_rows]
        p_predicted = [r['predicted'] for r in pv_rows]

        fig.add_trace(
            go.Bar(x=p_dates, y=p_actual, name='PV Actual', marker_color='#5cb85c'),
            row=3, col=1
        )
        fig.add_trace(
            go.Bar(x=p_dates, y=p_predicted, name='PV Predicted (ML)', marker_color='#5bc0de'),
            row=3, col=1
        )

    # Update Layout
    fig.update_layout(
        height=950,
        barmode='group',
        showlegend=True,
        margin=dict(l=50, r=50, t=60, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified"
    )

    grid_style = dict(showgrid=True, gridwidth=1, gridcolor='#e5e5e5')
    fig.update_xaxes(**grid_style)
    fig.update_yaxes(**grid_style)

    if f_dates:
        forecast_start_ts = f_dates[0].timestamp() * 1000
        fig.add_vline(
            x=forecast_start_ts, 
            line_width=1, line_dash="dash", line_color="gray",
            annotation_text="Forecast Start", annotation_position="top left"
        )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)