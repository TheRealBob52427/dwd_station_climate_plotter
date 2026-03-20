import os
import pandas as pd
import torch
import numpy as np
import matplotlib.pyplot as plt
from chronos import Chronos2Pipeline
from huggingface_hub import login

def apply_physical_constraints(pred_df):
    """
    Ensures forecasts stay within physically possible boundaries.
    - Rain (mm): Cannot be negative.
    - Sun (h): Must be between 0 and 1 (max 1 hour of sun per hour).
    - Wind (m/s): Cannot be negative.
    """
    # 1. Identify only the quantile columns (e.g., '0.1', '0.5', '0.9')
    # These are usually the columns that can be converted to numeric
    cols_to_fix = [c for c in pred_df.columns if c not in ['item_id', 'timestamp']]
    
    # 2. Ensure these columns are numeric (float)
    for col in cols_to_fix:
        pred_df[col] = pd.to_numeric(pred_df[col], errors='coerce')

    # 3. Apply masks and clip
    # Rain and Wind >= 0
    rain_wind_mask = pred_df['item_id'].str.contains('Rain|Wind')
    pred_df.loc[rain_wind_mask, cols_to_fix] = pred_df.loc[rain_wind_mask, cols_to_fix].clip(lower=0)

    # Sun between 0 and 1
    sun_mask = pred_df['item_id'].str.contains('Sun')
    pred_df.loc[sun_mask, cols_to_fix] = pred_df.loc[sun_mask, cols_to_fix].clip(lower=0, upper=1.0)

    return pred_df


def prepare_dwd_data():
    """Loads and prepares the DWD Köln/Bonn dataset, downloading it if necessary."""
    csv_path = "koeln_bonn_weather.csv"
    
    # --- AUTO-DOWNLOAD LOGIC ---
    if not os.path.exists(csv_path):
        print(f"'{csv_path}' not found. Downloading via wetterdienst...")
        try:
            from wetterdienst.provider.dwd.observation import DwdObservationRequest
        except ImportError:
            raise ImportError(
                "The 'wetterdienst' library is required to download the data automatically. "
                "Please install it using: pip install wetterdienst polars"
            )

        # Define the request for Station 02667 (Köln/Bonn) using the updated API
        request = DwdObservationRequest(
            parameters=[
                ("hourly", "temperature_air"),
                ("hourly", "precipitation"),
                ("hourly", "sun"),
                ("hourly", "wind")
            ],
            periods="historical"
        ).filter_by_station_id(station_id=["02667"])

        # Fetch data (returns a polars DataFrame, convert to pandas)
        print("Fetching historical data from DWD... this may take a moment.")
        df_long = request.values.all().df.to_pandas()

        # Wetterdienst returns data in a "long" format. Pivot it to "wide" format.
        df_wide = df_long.pivot_table(
            index="date",
            columns="parameter",
            values="value"
        ).reset_index()

        # Save to CSV so we don't have to download it again on the next run
        df_wide.to_csv(csv_path, index=False)
        print(f"Data successfully saved to '{csv_path}'.")
    # ---------------------------

    # Load the CSV (either pre-existing or just downloaded)
    df = pd.read_csv(csv_path)
    
    # 1. Parse timestamps (Wetterdienst exports ISO 8601 dates with UTC timezone)
    df['timestamp'] = pd.to_datetime(df['date'], utc=True).dt.tz_localize(None)
    
    # 2. Map standard wetterdienst parameters to your requested target names
    rename_mapping = {
        'temperature_air_mean_200': 'Temp (°C)',
        'temperature_air_mean_2m': 'Temp (°C)',
        'precipitation_height': 'Rain (mm)',
        'sunshine_duration': 'Sun (h)',
        'wind_speed': 'Wind (m/s)'
    }
    df = df.rename(columns=rename_mapping)
    
    # 3. Data correction: DWD records sunshine duration in minutes. Convert to hours.
    if 'Sun (h)' in df.columns and df['Sun (h)'].max() > 60:
        df['Sun (h)'] = df['Sun (h)'] / 60.0 
    
    # 4. Select Base Weather Features
    weather_features = ['timestamp', 'Temp (°C)', 'Rain (mm)', 'Sun (h)', 'Wind (m/s)']
    
    missing_cols = [col for col in weather_features if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing expected columns from DWD data: {missing_cols}. Current columns: {list(df.columns)}")
        
    df = df[weather_features]
    
    # Drop initial historical rows where main sensors weren't active yet
    df = df.dropna(subset=['Temp (°C)'])
    
    # 5. Resample to strict 1-hour intervals BEFORE adding time covariates
    print("Resampling data to strict 1-hour intervals...")
    df = df.set_index('timestamp').resample('1h').mean().ffill().reset_index()
    
    # --- ADD CYCLICAL TIME COVARIATES ---
    # We add these after resampling so the sine/cosine waves are mathematically perfect
    # and not distorted by forward-filling missing rows.
    df['Hour_sin'] = np.sin(2 * np.pi * df['timestamp'].dt.hour / 24.0)
    df['Hour_cos'] = np.cos(2 * np.pi * df['timestamp'].dt.hour / 24.0)
    df['Day_sin'] = np.sin(2 * np.pi * df['timestamp'].dt.dayofyear / 365.25)
    df['Day_cos'] = np.cos(2 * np.pi * df['timestamp'].dt.dayofyear / 365.25)
    # ------------------------------------

    df['id'] = 'Koeln_Bonn_Station'
    
    # Split 80/20
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    
    return train_df, test_df

def plot_multivariate_forecast(ctx_df, true_df, pred_df, is_zeroshot, weather_targets):
    """Visualizes the forecast for all predicted weather targets in a 2x2 grid."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.flatten()
    
    for i, target in enumerate(weather_targets):
        ax = axes[i]
        
        plot_ctx = ctx_df.iloc[-100:]
        target_id = f"Koeln_Bonn_Station_{target}"
        target_pred_df = pred_df[pred_df['item_id'] == target_id]
        
        ax.plot(plot_ctx['timestamp'], plot_ctx[target], label="Historical", color="black")
        ax.plot(true_df['timestamp'], true_df[target], label="True Future", color="green", linestyle="--")
        
        ax.plot(target_pred_df['timestamp'], target_pred_df['0.5'], label="Median Forecast", color="blue")
        ax.fill_between(
            target_pred_df['timestamp'], target_pred_df['0.1'], target_pred_df['0.9'], 
            color="blue", alpha=0.2, label="80% CI"
        )

        start_time = target_pred_df['timestamp'].iloc[0]
        ax.axvline(x=start_time, color='gray', linestyle=':', label='Forecast Start')
        
        ax.set_title(f"{target} Forecast")
        ax.set_xlabel("Date & Time")
        ax.grid(True, alpha=0.3)
        if i == 0:
            ax.legend()
    
    mode_str = "Zero-Shot" if is_zeroshot else "Fine-Tuned (Cross-Learning + Covariates)"
    fig.suptitle(f"Köln/Bonn Weather: Native Multivariate Forecast ({mode_str})", fontsize=16)
    plt.tight_layout()
    plt.savefig("koeln_bonn_multivariate_forecast.png", dpi=300, bbox_inches='tight')
    print("Saved plot to 'koeln_bonn_multivariate_forecast.png'")

def main(prediction_length=48, context_length=2048, zero_shot=False):
    print("Logging into Hugging Face...")
    hf_token = os.getenv("HF_TOKEN")
    if hf_token is None:
        raise ValueError("HF_TOKEN environment variable not found!")
    login(token=hf_token)

    print("Preparing dataset...")
    train_df, test_df = prepare_dwd_data()
    
    # Define Targets
    weather_targets = ['Temp (°C)', 'Rain (mm)', 'Sun (h)', 'Wind (m/s)']
    time_targets = ['Hour_sin', 'Hour_cos', 'Day_sin', 'Day_cos']
    all_targets = weather_targets + time_targets

    print("Loading Chronos-2 model...")
    pipeline = Chronos2Pipeline.from_pretrained(
        "amazon/chronos-2",
        device_map="cuda" if torch.cuda.is_available() else "cpu",
        torch_dtype=torch.bfloat16
    )

    if zero_shot:
        print("\n--- ZERO-SHOT MODE ACTIVE ---")
        active_pipeline = pipeline
    else:
        print("\n--- FINE-TUNING MODE ACTIVE (Optimized Hyperparameters) ---")
        train_matrix = train_df[all_targets].values.T
        dataset = [{"target": train_matrix}]
        
        # Optimized for local weather station convergence
        active_pipeline = pipeline.fit(
            dataset,
            context_length=context_length,
            prediction_length=prediction_length,          
            learning_rate=5e-5,   # Slightly lower to avoid overshooting local minima
            num_steps=250,        # Increased to allow for more granular convergence
            batch_size=64,                 
        )
        print("Fine-tuning complete!\n")
        
        save_directory = "./chronos_dwd_finetuned"
        os.makedirs(save_directory, exist_ok=True)

        print(f"Saving fine-tuned model to {save_directory}...")
        active_pipeline.model.save_pretrained(save_directory)
        if hasattr(active_pipeline.model, "config"):
            active_pipeline.model.config.save_pretrained(save_directory)

        print("Model saved successfully!")         

    print(f"Running rolling evaluation over {prediction_length}-hour windows...")
    offsets = [0, 500, 1000, 1500, 2000]
    
    maes = {t: [] for t in weather_targets}
    rmses = {t: [] for t in weather_targets}
    plot_ctx, plot_true, plot_pred = None, None, None

    for offset in offsets:
        end_idx = len(test_df) - offset
        
        ctx_start = end_idx - prediction_length - context_length
        ctx_end = end_idx - prediction_length
        
        ctx_df = test_df.iloc[ctx_start:ctx_end]
        true_f_df = test_df.iloc[ctx_end:end_idx]
        
        # Melt ALL targets into the context window so the model sees the time covariates
        long_ctx_df = ctx_df.melt(
            id_vars=['id', 'timestamp'], 
            value_vars=all_targets,
            var_name='target_col', 
            value_name='target_val'
        )
        long_ctx_df['item_id'] = long_ctx_df['id'] + '_' + long_ctx_df['target_col']
        
        pred_df = active_pipeline.predict_df(
            long_ctx_df, 
            prediction_length=prediction_length,
            quantile_levels=[0.1, 0.5, 0.9],
            id_column='item_id',
            timestamp_column='timestamp',
            target='target_val',
            cross_learning=True,
            batch_size=100
        )
        
        pred_df = apply_physical_constraints(pred_df)
                
        print(f"\nOffset -{offset} hours:")
        # Only calculate errors and print for the WEATHER variables
        for target in weather_targets:
            target_id = f"Koeln_Bonn_Station_{target}"
            med = pred_df[pred_df['item_id'] == target_id]['0.5'].values
            true_f = true_f_df[target].values
            
            window_mae = np.mean(np.abs(med - true_f))
            window_rmse = np.sqrt(np.mean((med - true_f)**2))
            
            maes[target].append(window_mae)
            rmses[target].append(window_rmse)
            
            print(f"  {target} -> MAE: {window_mae:.2f} | RMSE: {window_rmse:.2f}")
        
        if offset == 0:
            plot_ctx, plot_true, plot_pred = ctx_df, true_f_df, pred_df

    print("\n=== FINE-TUNED MULTIVARIATE EVALUATION ===")
    for target in weather_targets:
        print(f"{target} - Avg MAE: {np.mean(maes[target]):.2f} | Avg RMSE: {np.mean(rmses[target]):.2f}")
    print("==========================================\n")

    print("Plotting the most recent forecast window...")
    plot_multivariate_forecast(plot_ctx, plot_true, plot_pred, zero_shot, weather_targets)

if __name__ == "__main__":
    main(prediction_length=48, context_length=2048, zero_shot=False)
