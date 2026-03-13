"""
Plotting module for the DWD Station Climate Plotter.
Generates interactive Plotly charts for weather data and PV yield visualization.
"""
import json
import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots

def create_plot(historical_rows, forecast_rows=None):
    if not historical_rows and not forecast_rows:
        return None

    hist_data = historical_rows[::-1] if historical_rows else []
    fore_data = forecast_rows if forecast_rows else []

    def get_cols(data):
        return (
            [r['date_obj'] for r in data],
            [r.get('temp') for r in data],
            [r.get('rain') or 0 for r in data],
            [r.get('sun') or 0 for r in data],
            [r.get('pv_actual') for r in data],    # Neue PV-Spalten
            [r.get('pv_predicted') for r in data]
        )

    h_dates, h_temps, h_rains, h_suns, h_pv_actual, h_pv_pred = get_cols(hist_data)
    f_dates, f_temps, f_rains, f_suns, f_pv_actual, f_pv_pred = get_cols(fore_data)

    fig = make_subplots(
        rows=3, cols=1, 
        shared_xaxes=True, vertical_spacing=0.08,
        subplot_titles=("Temperature Trend (°C)", "Rain (mm) & Sun (h)", "PV Yield (kWh) - Actual vs. Predicted")
    )

    # --- TOP PLOT: TEMPERATURE  ---
    if h_dates:
        fig.add_trace(go.Scatter(x=h_dates, y=h_temps, name='Temp (Hist)', mode='lines', line=dict(color='#d9534f', width=3)), row=1, col=1)
    if f_dates:
        if h_dates and h_temps[-1] is not None and f_temps[0] is not None:
            fig.add_trace(go.Scatter(x=[h_dates[-1], f_dates[0]], y=[h_temps[-1], f_temps[0]], showlegend=False, mode='lines', line=dict(color='#d9534f', dash='dot', width=2), hoverinfo='skip'), row=1, col=1)
        fig.add_trace(go.Scatter(x=f_dates, y=f_temps, name='Temp (Fcst)', mode='lines+markers', line=dict(color='#d9534f', dash='dot', width=2), marker=dict(size=6)), row=1, col=1)

    # --- MIDDLE PLOT: RAIN & SUN  ---
    if h_dates:
        fig.add_trace(go.Bar(x=h_dates, y=h_rains, name='Rain', marker_color='#0275d8'), row=2, col=1)
        fig.add_trace(go.Bar(x=h_dates, y=h_suns, name='Sun', marker_color='#f0ad4e'), row=2, col=1)
    if f_dates:
        fig.add_trace(go.Bar(x=f_dates, y=f_rains, name='Rain (Fcst)', marker_color='#0275d8', opacity=0.4, showlegend=False), row=2, col=1)
        fig.add_trace(go.Bar(x=f_dates, y=f_suns, name='Sun (Fcst)', marker_color='#f0ad4e', opacity=0.4, showlegend=False), row=2, col=1)

    # --- BOTTOM PLOT: PV YIELD ---
    if h_dates:
        fig.add_trace(go.Bar(x=h_dates, y=h_pv_actual, name='PV Actual (Hist)', marker_color='#5cb85c'), row=3, col=1)
        fig.add_trace(go.Bar(x=h_dates, y=h_pv_pred, name='PV Predicted (Hist)', marker_color='#5bc0de'), row=3, col=1)
        
    if f_dates:
        # Forecast PV Yield wird halbtransparent gezeichnet
        fig.add_trace(go.Bar(x=f_dates, y=f_pv_pred, name='PV Predicted (Fcst)', marker_color='#5bc0de', opacity=0.4), row=3, col=1)

    fig.update_layout(
        height=950, barmode='group', showlegend=True,
        margin=dict(l=50, r=50, t=60, b=50), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', hovermode="x unified"
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#e5e5e5')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#e5e5e5')

    if f_dates:
        fig.add_vline(x=f_dates[0].timestamp() * 1000, line_width=1, line_dash="dash", line_color="gray", annotation_text="Forecast Start", annotation_position="top left")

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)