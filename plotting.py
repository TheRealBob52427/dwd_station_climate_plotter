# plotting.py
import matplotlib
# 'Agg' is crucial for servers without a display (headless)
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

def create_plot(rows):
    """
    Creates a bar chart and returns it as a Base64 string.
    """
    if not rows:
        return None

    # Prepare data (Reverse order: Old -> New for time axis)
    plot_data = rows[::-1]

    dates = [r['date'][:5] for r in plot_data] # Day.Month only
    temps = [r['temp'] if r['temp'] is not None else 0 for r in plot_data]
    rains = [r['rain'] if r['rain'] is not None else 0 for r in plot_data]
    suns = [r['sun'] if r['sun'] is not None else 0 for r in plot_data]

    # Create Figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # 1. Plot: Temperature
    ax1.bar(dates, temps, color='#d9534f', alpha=0.7, label='Temp (°C)')
    ax1.set_ylabel('Temp (°C)')
    ax1.set_title('Temperature Trend')
    ax1.grid(True, axis='y', linestyle='--', alpha=0.5)
    ax1.legend()

    # 2. Plot: Rain & Sun (Grouped Bars)
    x = range(len(dates))
    width = 0.4

    ax2.bar([i - width/2 for i in x], rains, width, label='Rain (mm)', color='#0275d8')
    ax2.bar([i + width/2 for i in x], suns, width, label='Sun (h)', color='#f0ad4e')

    ax2.set_ylabel('Amount')
    ax2.set_xticks(x)
    ax2.set_xticklabels(dates, rotation=45)
    ax2.legend()
    ax2.grid(True, axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()

    # Save to Buffer
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close() # Free memory

    return plot_url
