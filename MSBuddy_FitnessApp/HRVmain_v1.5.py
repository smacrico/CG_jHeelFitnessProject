import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import welch
from scipy.interpolate import interp1d

def calculate_ibi(timestamps_ms):
    """Calculates inter-beat intervals (IBIs) in milliseconds from timestamps."""
    return np.diff(timestamps_ms)

def filter_ibi_artifacts(ibi, lower_threshold=300, upper_threshold=2000, method='range'):
    """Enhanced artifact filter with multiple methods."""
    if method == 'range':
        # Simple range filter
        valid_mask = (ibi >= lower_threshold) & (ibi <= upper_threshold)
    elif method == 'statistical':
        # Statistical outlier removal (more sophisticated)
        q1, q3 = np.percentile(ibi, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        valid_mask = (ibi >= max(lower_bound, lower_threshold)) & (ibi <= min(upper_bound, upper_threshold))
    
    return ibi[valid_mask], valid_mask

def calculate_time_domain_hrv(ibi):
    """Calculates time-domain HRV metrics with enhanced error handling."""
    if len(ibi) < 2:
        return {"sdnn": np.nan, "rmssd": np.nan, "nn50": np.nan, "pnn50": np.nan, "mean_ibi": np.nan}
    
    diff_ibi = np.diff(ibi)
    
    metrics = {
        "sdnn": np.std(ibi, ddof=1),  # Use sample standard deviation
        "rmssd": np.sqrt(np.mean(diff_ibi**2)),
        "nn50": np.sum(np.abs(diff_ibi) > 50),
        "pnn50": (np.sum(np.abs(diff_ibi) > 50) / len(diff_ibi)) * 100 if len(diff_ibi) > 0 else np.nan,
        "mean_ibi": np.mean(ibi)
    }
    
    return metrics

def interpolate_ibi_for_frequency_analysis(ibi, target_fs=4.0):
    """
    Interpolates IBI data to create evenly sampled time series for frequency analysis.
    
    Args:
        ibi: Inter-beat intervals in ms
        target_fs: Target sampling frequency in Hz
        
    Returns:
        interpolated_ibi: Evenly sampled IBI time series
        time_vector: Corresponding time vector
    """
    if len(ibi) < 4:  # Need minimum points for interpolation
        return None, None
    
    # Create cumulative time vector from IBIs
    cumulative_time = np.cumsum(np.concatenate([[0], ibi])) / 1000.0  # Convert to seconds
    
    # Create interpolation function
    f_interpolate = interp1d(cumulative_time[1:], ibi, kind='cubic', 
                           bounds_error=False, fill_value='extrapolate')
    
    # Create evenly spaced time vector
    total_duration = cumulative_time[-1]
    time_vector = np.arange(0, total_duration, 1.0/target_fs)
    
    # Remove last point if it's beyond our data
    if len(time_vector) > 0 and time_vector[-1] > cumulative_time[-1]:
        time_vector = time_vector[:-1]
    
    # Interpolate IBI values
    interpolated_ibi = f_interpolate(time_vector)
    
    return interpolated_ibi, time_vector

def calculate_frequency_domain_hrv(ibi, target_fs=4.0):
    """
    Enhanced frequency-domain HRV calculation with proper interpolation.
    """
    if len(ibi) < 10:  # Need sufficient data points
        return {"vlf": np.nan, "lf": np.nan, "hf": np.nan, "lf_hf_ratio": np.nan, 
                "total_power": np.nan, "lf_nu": np.nan, "hf_nu": np.nan}
    
    # Interpolate IBI data
    interpolated_ibi, time_vector = interpolate_ibi_for_frequency_analysis(ibi, target_fs)
    
    if interpolated_ibi is None or len(interpolated_ibi) < 64:
        return {"vlf": np.nan, "lf": np.nan, "hf": np.nan, "lf_hf_ratio": np.nan, 
                "total_power": np.nan, "lf_nu": np.nan, "hf_nu": np.nan}
    
    # Detrend the signal (remove DC component and linear trend)
    interpolated_ibi = interpolated_ibi - np.mean(interpolated_ibi)
    
    # Calculate PSD using Welch's method
    nperseg = min(256, len(interpolated_ibi) // 4)  # Adaptive window size
    frequencies, psd = welch(interpolated_ibi, fs=target_fs, nperseg=nperseg, 
                           overlap=nperseg//2, window='hann')
    
    # Define frequency bands (standard HRV bands)
    vlf_band = (frequencies >= 0.0033) & (frequencies < 0.04)
    lf_band = (frequencies >= 0.04) & (frequencies < 0.15)
    hf_band = (frequencies >= 0.15) & (frequencies <= 0.4)
    
    # Calculate power in each band using trapezoidal integration
    vlf_power = np.trapz(psd[vlf_band], frequencies[vlf_band]) if np.any(vlf_band) else 0
    lf_power = np.trapz(psd[lf_band], frequencies[lf_band]) if np.any(lf_band) else 0
    hf_power = np.trapz(psd[hf_band], frequencies[hf_band]) if np.any(hf_band) else 0
    
    total_power = vlf_power + lf_power + hf_power
    
    # Calculate normalized units and ratios
    lf_nu = (lf_power / (lf_power + hf_power)) * 100 if (lf_power + hf_power) > 0 else np.nan
    hf_nu = (hf_power / (lf_power + hf_power)) * 100 if (lf_power + hf_power) > 0 else np.nan
    lf_hf_ratio = lf_power / hf_power if hf_power > 0 else np.nan
    
    return {
        "vlf": vlf_power,
        "lf": lf_power, 
        "hf": hf_power,
        "total_power": total_power,
        "lf_hf_ratio": lf_hf_ratio,
        "lf_nu": lf_nu,
        "hf_nu": hf_nu
    }

def calculate_enhanced_hrv_score(time_domain_metrics, frequency_domain_metrics, 
                               baseline_rmssd=45, baseline_sdnn=50):
    """
    Enhanced HRV score calculation with personalized baselines.
    Particularly important for MS patients who may have different normal ranges.
    """
    if not time_domain_metrics or not frequency_domain_metrics:
        return np.nan
    
    score = 0
    total_weight = 0
    
    # Weights (can be adjusted based on research or personal preference)
    weights = {
        'rmssd': 0.35,
        'sdnn': 0.25, 
        'hf': 0.20,
        'lf_hf_ratio': 0.20
    }
    
    # RMSSD score (parasympathetic activity indicator)
    rmssd = time_domain_metrics.get("rmssd", np.nan)
    if not np.isnan(rmssd):
        # Use personalized baseline instead of fixed range
        rmssd_score = min(100, max(0, (rmssd / baseline_rmssd) * 100))
        score += rmssd_score * weights['rmssd']
        total_weight += weights['rmssd']
    
    # SDNN score (overall HRV)
    sdnn = time_domain_metrics.get("sdnn", np.nan)
    if not np.isnan(sdnn):
        sdnn_score = min(100, max(0, (sdnn / baseline_sdnn) * 100))
        score += sdnn_score * weights['sdnn']
        total_weight += weights['sdnn']
    
    # HF power score (parasympathetic activity)
    hf = frequency_domain_metrics.get("hf", np.nan)
    if not np.isnan(hf):
        # Logarithmic scaling for HF power
        hf_score = min(100, max(0, np.log10(max(1, hf)) * 20))
        score += hf_score * weights['hf']
        total_weight += weights['hf']
    
    # LF/HF ratio score (autonomic balance - lower is generally better for recovery)
    lf_hf = frequency_domain_metrics.get("lf_hf_ratio", np.nan)
    if not np.isnan(lf_hf):
        # Inverse relationship: lower LF/HF ratio = higher score
        lf_hf_score = max(0, min(100, 100 - (lf_hf * 25)))  # Scale so ratio of 4 = 0 points
        score += lf_hf_score * weights['lf_hf_ratio']
        total_weight += weights['lf_hf_ratio']
    
    # Normalize by actual weights used
    if total_weight > 0:
        final_score = score / total_weight
    else:
        final_score = np.nan
    
    return final_score

# Test the enhanced version
def test_enhanced_hrv_analysis():
    """Test function with simulated data"""
    # Simulate more realistic IBI data
    np.random.seed(42)
    base_ibi = 900  # ~67 BPM
    n_beats = 300
    
    # Add realistic variability patterns
    trend = np.sin(np.linspace(0, 4*np.pi, n_beats)) * 50  # Respiratory variation
    noise = np.random.normal(0, 20, n_beats)  # Random variation
    ibi_data = base_ibi + trend + noise
    
    print("=== Enhanced HRV Analysis Results ===")
    
    # Filter artifacts
    ibi_filtered, _ = filter_ibi_artifacts(ibi_data, method='statistical')
    print(f"Filtered {len(ibi_data) - len(ibi_filtered)} artifacts from {len(ibi_data)} beats")
    
    # Calculate metrics
    time_metrics = calculate_time_domain_hrv(ibi_filtered)
    freq_metrics = calculate_frequency_domain_hrv(ibi_filtered)
    
    print("\nTime Domain Metrics:")
    for key, value in time_metrics.items():
        print(f"  {key}: {value:.2f}" if not np.isnan(value) else f"  {key}: N/A")
    
    print("\nFrequency Domain Metrics:")
    for key, value in freq_metrics.items():
        print(f"  {key}: {value:.2f}" if not np.isnan(value) else f"  {key}: N/A")
    
    # Calculate enhanced score
    hrv_score = calculate_enhanced_hrv_score(time_metrics, freq_metrics)
    print(f"\nEnhanced HRV Score: {hrv_score:.1f}/100")
    
    return time_metrics, freq_metrics, hrv_score

if __name__ == "__main__":
    test_enhanced_hrv_analysis()
