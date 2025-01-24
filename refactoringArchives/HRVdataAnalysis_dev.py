import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class HRVAnalysis:
    def __init__(self):
        self.hrv_log = pd.DataFrame(columns=[
            'date', 'hrv', 'pnn50', 'pnn20', 'rmssd', 'sdnn',
            'hrv_diff_from_avg', 'oxygen_saturation',
            'average_hrv', 'recovery_score'
        ])
    
    def add_session(self, date, hrv, pnn50, pnn20, rmssd, sdnn,
                   hrv_diff_from_avg, oxygen_saturation, average_hrv, recovery_score):
        new_session = pd.DataFrame({
            'date': [date],
            'hrv': [hrv],
            'pnn50': [pnn50],
            'pnn20': [pnn20],
            'rmssd': [rmssd],
            'sdnn': [sdnn],
            'hrv_diff_from_avg': [hrv_diff_from_avg],
            'oxygen_saturation': [oxygen_saturation],
            'average_hrv': [average_hrv],
            'recovery_score': [recovery_score]
        })
        
        self.hrv_log = pd.concat([self.hrv_log, new_session], ignore_index=True)
    
    def visualize_hrv_metrics(self):
        plt.style.use('seaborn')
        fig = plt.figure(figsize=(15, 12))
        
        # Plot 1: HRV Trend with Average
        plt.subplot(2, 2, 1)
        plt.plot(self.hrv_log['date'], self.hrv_log['hrv'], 'b-o', label='HRV')
        plt.plot(self.hrv_log['date'], self.hrv_log['average_hrv'], 'r--', label='Average HRV')
        plt.title('HRV Trend Over Time')
        plt.xticks(rotation=45)
        plt.legend()
        
        # Plot 2: PNN metrics
        plt.subplot(2, 2, 2)
        plt.plot(self.hrv_log['date'], self.hrv_log['pnn50'], 'g-o', label='pNN50')
        plt.plot(self.hrv_log['date'], self.hrv_log['pnn20'], 'y-o', label='pNN20')
        plt.title('PNN Metrics Over Time')
        plt.xticks(rotation=45)
        plt.legend()
        
        # Plot 3: RMSSD and SDNN
        plt.subplot(2, 2, 3)
        plt.plot(self.hrv_log['date'], self.hrv_log['rmssd'], 'm-o', label='RMSSD')
        plt.plot(self.hrv_log['date'], self.hrv_log['sdnn'], 'c-o', label='SDNN')
        plt.title('RMSSD and SDNN Over Time')
        plt.xticks(rotation=45)
        plt.legend()
        
        # Plot 4: Recovery Score vs HRV
        plt.subplot(2, 2, 4)
        plt.scatter(self.hrv_log['recovery_score'], self.hrv_log['hrv'])
        plt.title('Recovery Score vs HRV')
        plt.xlabel('Recovery Score')
        plt.ylabel('HRV')
        
        plt.tight_layout()
        plt.show()
    
    def analyze_recovery_state(self, current_hrv, average_hrv):
        hrv_diff = current_hrv - average_hrv
        if hrv_diff > 5:
            return "Well recovered"
        elif hrv_diff < -5:
            return "Need more recovery"
        else:
            return "Moderate recovery state"

# Example usage with your current data
analysis = HRVAnalysis()

# Adding your current session data
analysis.add_session(
    date=datetime.now(),
    hrv=43.81,
    pnn50=7.2,
    pnn20=20.3,
    rmssd=11.28,
    sdnn=21.25,
    hrv_diff_from_avg=-21.00,
    oxygen_saturation=-1.0,
    average_hrv=65.72,
    recovery_score=53
)

# Add some example historical data (you would replace with your actual historical data)
for i in range(7):
    analysis.add_session(
        date=datetime.now() - pd.Timedelta(days=i),
        hrv=43.81 + np.random.normal(0, 5),
        pnn50=7.2 + np.random.normal(0, 1),
        pnn20=20.3 + np.random.normal(0, 2),
        rmssd=11.28 + np.random.normal(0, 1),
        sdnn=21.25 + np.random.normal(0, 2),
        hrv_diff_from_avg=-21.00 + np.random.normal(0, 5),
        oxygen_saturation=-1.0 + np.random.normal(0, 0.5),
        average_hrv=65.72,
        recovery_score=53 + np.random.normal(0, 5)
    )

# Generate visualizations
analysis.visualize_hrv_metrics()

# Calculate current recovery state
current_state = analysis.analyze_recovery_state(43.81, 65.72)
print(f"\nCurrent Recovery State: {current_state}")

# Print summary statistics
print("\nSummary Statistics:")
print(analysis.hrv_log.describe())