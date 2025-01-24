# I'll modify the previous code to include these additional HRV metrics, particularly the frequency domain measures (VLF, LF, HF)
# and time domain measures (SD1, SD2). Here's the enhanced version:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class EnhancedHRVAnalysis:
    def __init__(self):
        self.hrv_log = pd.DataFrame(columns=[
            'date', 'sd1', 'sd2', 'sd2_sd1_ratio', 'sdnn',
            'mean_rr', 'mean_hr', 'rmssd', 'pnn50',
            'vlf', 'lf', 'hf', 'lf_hf_ratio', 'lf_nu', 'hf_nu'
        ])
    
    def add_session(self, date, sd1, sd2, sdnn, mean_rr, mean_hr,
                   rmssd, pnn50, vlf, lf, hf, lf_nu, hf_nu):
        new_session = pd.DataFrame({
            'date': [date],
            'sd1': [sd1],
            'sd2': [sd2],
            'sd2_sd1_ratio': [sd2/sd1],
            'sdnn': [sdnn],
            'mean_rr': [mean_rr],
            'mean_hr': [mean_hr],
            'rmssd': [rmssd],
            'pnn50': [pnn50],
            'vlf': [vlf],
            'lf': [lf],
            'hf': [hf],
            'lf_hf_ratio': [lf/hf],
            'lf_nu': [lf_nu],
            'hf_nu': [hf_nu]
        })
        
        self.hrv_log = pd.concat([self.hrv_log, new_session], ignore_index=True)
    
    def visualize_comprehensive_hrv(self):
        plt.style.use('seaborn')
        fig = plt.figure(figsize=(20, 15))
        
        # Plot 1: Poincaré Plot Indices (SD1, SD2)
        plt.subplot(3, 2, 1)
        plt.plot(self.hrv_log['date'], self.hrv_log['sd1'], 'b-o', label='SD1')
        plt.plot(self.hrv_log['date'], self.hrv_log['sd2'], 'r-o', label='SD2')
        plt.title('Poincaré Plot Indices Over Time')
        plt.xticks(rotation=45)
        plt.legend()
        
        # Plot 2: Frequency Domain Measures
        plt.subplot(3, 2, 2)
        plt.plot(self.hrv_log['date'], self.hrv_log['vlf'], 'g-o', label='VLF')
        plt.plot(self.hrv_log['date'], self.hrv_log['lf'], 'b-o', label='LF')
        plt.plot(self.hrv_log['date'], self.hrv_log['hf'], 'r-o', label='HF')
        plt.title('Frequency Domain Measures')
        plt.xticks(rotation=45)
        plt.legend()
        
        # Plot 3: Autonomic Balance
        plt.subplot(3, 2, 3)
        plt.plot(self.hrv_log['date'], self.hrv_log['lf_hf_ratio'], 'p-o')
        plt.title('LF/HF Ratio (Autonomic Balance)')
        plt.xticks(rotation=45)
        
        # Plot 4: Normalized Units
        plt.subplot(3, 2, 4)
        plt.plot(self.hrv_log['date'], self.hrv_log['lf_nu'], 'b-o', label='LF (n.u.)')
        plt.plot(self.hrv_log['date'], self.hrv_log['hf_nu'], 'r-o', label='HF (n.u.)')
        plt.title('Normalized Units of LF and HF')
        plt.xticks(rotation=45)
        plt.legend()
        
        # Plot 5: Time Domain Measures
        plt.subplot(3, 2, 5)
        plt.plot(self.hrv_log['date'], self.hrv_log['rmssd'], 'g-o', label='RMSSD')
        plt.plot(self.hrv_log['date'], self.hrv_log['sdnn'], 'b-o', label='SDNN')
        plt.title('Time Domain Measures')
        plt.xticks(rotation=45)
        plt.legend()
        
        # Plot 6: Heart Rate and RR Intervals
        ax1 = plt.subplot(3, 2, 6)
        ax2 = ax1.twinx()
        ax1.plot(self.hrv_log['date'], self.hrv_log['mean_hr'], 'b-o', label='Mean HR')
        ax2.plot(self.hrv_log['date'], self.hrv_log['mean_rr'], 'r-o', label='Mean RR')
        plt.title('Heart Rate and RR Intervals')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.show()
    
    def analyze_hrv_status(self):
        latest = self.hrv_log.iloc[-1]
        
        analysis = {
            'Autonomic Balance': 'Balanced' if 0.5 <= latest['lf_hf_ratio'] <= 2 else 
                               'Sympathetic Dominant' if latest['lf_hf_ratio'] > 2 else 
                               'Parasympathetic Dominant',
            'Stress Level': 'Normal' if latest['sd2_sd1_ratio'] < 4 else 'Elevated',
            'Recovery Status': 'Good' if latest['rmssd'] > 20 else 'Needs Improvement'
        }
        
        return analysis

# Example usage with your current data
analysis = EnhancedHRVAnalysis()

# Adding your current session data
analysis.add_session(
    date=datetime.now(),
    sd1=22,
    sd2=77,
    sdnn=56.49,
    mean_rr=860,
    mean_hr=70,
    rmssd=32,
    pnn50=7,
    vlf=170,
    lf=130,
    hf=108,
    lf_nu=0.55,
    hf_nu=0.45
)

# Generate analysis
status = analysis.analyze_hrv_status()
print("\nHRV Status Analysis:")
for key, value in status.items():
    print(f"{key}: {value}")

# Generate visualizations
analysis.visualize_comprehensive_hrv()