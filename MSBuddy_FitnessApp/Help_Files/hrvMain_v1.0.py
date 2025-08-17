import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import welch

def calculate_ibi(timestamps_ms):
    """Calculates inter-beat intervals (IBIs) in milliseconds from timestamps."""
    return np.diff(timestamps_ms)

def filter_ibi_artifacts(ibi, lower_threshold=300, upper_threshold=2000):
    """Simple artifact filter: removes IBIs outside a reasonable range (ms).
    Adjust thresholds based on your data characteristics.
    """
    return ibi[(ibi >= lower_threshold) & (ibi <= upper_threshold)]

def calculate_time_domain_hrv(ibi):
    """Calculates common time-domain HRV metrics."""
    if len(ibi) < 2:
        return {"sdnn": np.nan, "rmssd": np.nan, "nn50": np.nan, "pnn50": np.nan}
    diff_ibi = np.diff(ibi)
    sdnn = np.std(ibi)
    rmssd = np.sqrt(np.mean(diff_ibi**2))
    nn50 = np.sum(np.abs(diff_ibi) > 50)
    pnn50 = (nn50 / len(diff_ibi)) * 100
    return {"sdnn": sdnn, "rmssd": rmssd, "nn50": nn50, "pnn50": pnn50}

def calculate_frequency_domain_hrv(ibi, sampling_rate=4):
    """Calculates common frequency-domain HRV metrics using Welch's method."""
    if len(ibi) < 2:
        return {"vlf": np.nan, "lf": np.nan, "hf": np.nan, "lf_hf_ratio": np.nan}
    ibi_sec = np.array(ibi) / 1000
    frequencies, power_spectral_density = welch(ibi_sec, fs=sampling_rate, nperseg=256) # Adjust parameters as needed

    vlf_power = np.trapz(power_spectral_density[(frequencies >= 0.0033) & (frequencies < 0.04)], frequencies[(frequencies >= 0.0033) & (frequencies < 0.04)])
    lf_power = np.trapz(power_spectral_density[(frequencies >= 0.04) & (frequencies < 0.15)], frequencies[(frequencies >= 0.04) & (frequencies < 0.15)])
    hf_power = np.trapz(power_spectral_density[(frequencies >= 0.15) & (frequencies <= 0.4)], frequencies[(frequencies >= 0.15) & (frequencies <= 0.4)])
    lf_hf_ratio = lf_power / hf_power if hf_power > 0 else np.nan

    return {"vlf": vlf_power, "lf": lf_power, "hf": hf_power, "lf_hf_ratio": lf_hf_ratio}

def calculate_hrv_score(time_domain_metrics, frequency_domain_metrics):
    """
    A simplified function to calculate a combined HRV score.
    This is a heuristic approach and can be adjusted based on your preferences
    and understanding of HRV.
    """
    score = 0
    weight_rmssd = 0.3
    weight_sdnn = 0.3
    weight_hf = 0.3
    weight_lf_hf = 0.1

    # Normalize and weight RMSSD (rough healthy range: 20-100 ms)
    rmssd = time_domain_metrics.get("rmssd", np.nan)
    if not np.isnan(rmssd):
        normalized_rmssd = np.clip((rmssd - 20) / 80, 0, 1)
        score += normalized_rmssd * weight_rmssd

    # Normalize and weight SDNN (rough healthy range: 40-150 ms)
    sdnn = time_domain_metrics.get("sdnn", np.nan)
    if not np.isnan(sdnn):
        normalized_sdnn = np.clip((sdnn - 40) / 110, 0, 1)
        score += normalized_sdnn * weight_sdnn

    # Normalize and weight HF power (no strict range, scale to observed range)
    hf = frequency_domain_metrics.get("hf", np.nan)
    if not np.isnan(hf):
        max_hf = 1000 # Adjust based on your data
        normalized_hf = np.clip(hf / max_hf, 0, 1)
        score += normalized_hf * weight_hf

    # Normalize and weight LF/HF ratio (lower is often better, e.g., < 2)
    lf_hf = frequency_domain_metrics.get("lf_hf_ratio", np.nan)
    if not np.isnan(lf_hf):
        normalized_lf_hf = np.clip(1 - (lf_hf / 2), 0, 1)
        score -= normalized_lf_hf * weight_lf_hf

    final_hrv_score = np.clip(score * 100, 0, 100)
    return final_hrv_score

def visualize_hrv_metrics(time_domain, frequency_domain, final_score):
    """Visualizes the calculated HRV metrics and the final score."""
    metrics = {**time_domain, **frequency_domain, "HRV Score": final_score}
    metric_names = list(metrics.keys())
    metric_values = list(metrics.values())

    normal_ranges = {
        "sdnn": (40, 150),
        "rmssd": (20, 100),
        "hf": (0, 800), # Example range, adjust based on your data
        "lf_hf_ratio": (0, 3), # Example range
        "nn50": (0, np.inf), # Higher is generally better
        "pnn50": (0, np.inf), # Higher is generally better
        "vlf": (0, np.inf),
        "lf": (0, np.inf),
        "HRV Score": (50, 80) # Example range for the final score
    }

    colors = []
    for name, value in metrics.items():
        if name in normal_ranges and not np.isnan(value):
            lower, upper = normal_ranges[name]
            if not (lower <= value <= upper):
                colors.append('red')
            else:
                colors.append('skyblue')
        else:
            colors.append('skyblue') # Color unknown ranges blue

    plt.figure(figsize=(10, 6))
    bars = plt.bar(metric_names, metric_values, color=colors)
    plt.ylabel("Value")
    plt.title("Calculated HRV Metrics and Score")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Add annotations for values
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.05 * max(metric_values),
                 f'{yval:.2f}' if not np.isnan(yval) else 'NaN', ha='center', va='bottom')

    plt.show()

# --- Example Usage (assuming you have 'timestamps_ms' - replace with your actual data loading) ---
# Let's simulate some timestamp data (replace with your Garmin data loading)
np.random.seed(42)
average_hr = 65  # BPM
num_beats = 300
time_interval_seconds = num_beats * 60 / average_hr
start_time = 0
timestamps_sec = np.sort(np.random.uniform(start_time, start_time + time_interval_seconds, num_beats))
ibi_ms_simulated = np.diff(timestamps_sec) * 1000 + np.random.normal(0, 15, num_beats - 1) # Add some variability
timestamps_ms = np.cumsum(ibi_ms_simulated) # Reconstruct timestamps

# 1. Calculate IBIs
ibi_ms = calculate_ibi(timestamps_ms)

# 2. Filter artifacts
ibi_filtered = filter_ibi_artifacts(ibi_ms)

# 3. Calculate time-domain HRV metrics
time_domain_hrv = calculate_time_domain_hrv(ibi_filtered)
print("Time-Domain HRV Metrics:", time_domain_hrv)

# 4. Calculate frequency-domain HRV metrics
if len(ibi_filtered) > 1:
    average_ibi_ms = np.mean(ibi_filtered)
    sampling_rate = 1000 / average_ibi_ms if average_ibi_ms > 0 else 4
    frequency_domain_hrv = calculate_frequency_domain_hrv(ibi_filtered, sampling_rate)
    print("Frequency-Domain HRV Metrics:", frequency_domain_hrv)

    # 5. Calculate the final HRV score
    final_score = calculate_hrv_score(time_domain_hrv, frequency_domain_hrv)
    print("Final HRV Score (Simplified):", f"{final_score:.2f}")

    # 6. Visualize the metrics
    visualize_hrv_metrics(time_domain_hrv, frequency_domain_hrv, final_score)

else:
    print("Insufficient data for frequency-domain HRV calculation and final score.")