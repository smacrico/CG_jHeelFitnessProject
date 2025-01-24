from fitparse import FitFile
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os

class FitFileParser:
    def __init__(self):
        self.raw_data = []
        self.hrv_data = []
        self.rr_intervals = []
    
    def parse_fit_file(self, fit_file_path):
        """Parse FIT file and extract HRV related data"""
        try:
            fitfile = FitFile(fit_file_path)
            
            # Extract HRV data
            for record in fitfile.get_messages('hrv'):
                hrv_data = record.get_values()
                if 'time' in hrv_data:
                    self.rr_intervals.extend(hrv_data['time'])
            
            # Extract other metrics
            for record in fitfile.get_messages('record'):
                data = record.get_values()
                self.raw_data.append({
                    'timestamp': data.get('timestamp', None),
                    'heart_rate': data.get('heart_rate', None),
                    'speed': data.get('speed', None),
                    'distance': data.get('distance', None),
                    'temperature': data.get('temperature', None),
                    'altitude': data.get('altitude', None)
                })
                
            return True
            
        except Exception as e:
            print(f"Error parsing FIT file: {e}")
            return False

    def calculate_hrv_metrics(self):
        """Calculate HRV metrics from RR intervals"""
        if not self.rr_intervals:
            return None
            
        rr_intervals = np.array(self.rr_intervals) / 1000.0  # Convert to seconds
        
        # Time domain metrics
        sdnn = np.std(rr_intervals)
        rmssd = np.sqrt(np.mean(np.diff(rr_intervals) ** 2))
        mean_rr = np.mean(rr_intervals)
        mean_hr = 60 / mean_rr
        
        # Calculate pNN50
        differences = np.abs(np.diff(rr_intervals))
        pnn50 = 100 * np.sum(differences > 0.05) / len(differences)
        
        # Calculate SD1 and SD2 using Poincaré plot
        sd1 = np.std(np.diff(rr_intervals) / np.sqrt(2))
        sd2 = np.std(rr_intervals)
        
        # Frequency domain calculations
        from scipy import signal
        from scipy.integrate import simps
        
        # Resample RR intervals to regular time axis
        fs = 4.0  # Sample rate in Hz
        interpolated_time = np.arange(0, len(rr_intervals)) * np.mean(rr_intervals)
        interpolated_rr = np.interp(interpolated_time, 
                                  np.cumsum(rr_intervals), 
                                  rr_intervals)
        
        # Calculate power spectral density
        frequencies, psd = signal.welch(interpolated_rr, 
                                      fs=fs, 
                                      nperseg=256,
                                      nfft=2048)
        
        # Define frequency bands
        vlf_band = (0.0033, 0.04)
        lf_band = (0.04, 0.15)
        hf_band = (0.15, 0.4)
        
        # Calculate power in each band
        vlf = simps(psd[(frequencies >= vlf_band[0]) & 
                       (frequencies < vlf_band[1])], 
                   frequencies[(frequencies >= vlf_band[0]) & 
                             (frequencies < vlf_band[1])])
        
        lf = simps(psd[(frequencies >= lf_band[0]) & 
                      (frequencies < lf_band[1])], 
                  frequencies[(frequencies >= lf_band[0]) & 
                            (frequencies < lf_band[1])])
        
        hf = simps(psd[(frequencies >= hf_band[0]) & 
                      (frequencies < hf_band[1])], 
                  frequencies[(frequencies >= hf_band[0]) & 
                            (frequencies < hf_band[1])])
        
        # Calculate normalized units
        total_power = vlf + lf + hf
        lf_nu = lf / (lf + hf)
        hf_nu = hf / (lf + hf)
        lf_hf_ratio = lf / hf
        
        return {
            'sdnn': sdnn * 1000,  # Convert back to ms
            'rmssd': rmssd * 1000,
            'pnn50': pnn50,
            'mean_rr': mean_rr * 1000,
            'mean_hr': mean_hr,
            'sd1': sd1 * 1000,
            'sd2': sd2 * 1000,
            'vlf': vlf,
            'lf': lf,
            'hf': hf,
            'lf_nu': lf_nu,
            'hf_nu': hf_nu,
            'lf_hf_ratio': lf_hf_ratio
        }

class HRVAnalyzer:
    def __init__(self):
        self.parser = FitFileParser()
        self.hrv_database = pd.DataFrame()
        
    def process_fit_file(self, fit_file_path):
        """Process a single FIT file and add to database"""
        if self.parser.parse_fit_file(fit_file_path):
            metrics = self.parser.calculate_hrv_metrics()
            if metrics:
                metrics['date'] = datetime.now()  # Or extract from FIT file
                self.hrv_database = pd.concat([
                    self.hrv_database,
                    pd.DataFrame([metrics])
                ], ignore_index=True)
                return True
        return False
    
    def process_directory(self, directory_path):
        """Process all FIT files in a directory"""
        for file in os.listdir(directory_path):
            if file.endswith('.fit'):
                file_path = os.path.join(directory_path, file)
                self.process_fit_file(file_path)

    def save_database(self, filepath):
        """Save HRV database to CSV"""
        self.hrv_database.to_csv(filepath, index=False)
    
    def load_database(self, filepath):
        """Load HRV database from CSV"""
        self.hrv_database = pd.read_csv(filepath)

# Usage example:
def main():
    # Initialize analyzer
    analyzer = HRVAnalyzer()
    
    # Process FIT files
    fit_directory = "path/to/your/fit/files"
    analyzer.process_directory(fit_directory)
    
    # Save processed data
    analyzer.save_database("hrv_database.csv")
    
    # Create visualizations
    from previous_visualization_code import EnhancedHRVAnalysis
    
    hrv_analysis = EnhancedHRVAnalysis()
    
    # Add each session from the database
    for _, row in analyzer.hrv_database.iterrows():
        hrv_analysis.add_session(
            date=row['date'],
            sd1=row['sd1'],
            sd2=row['sd2'],
            sdnn=row['sdnn'],
            mean_rr=row['mean_rr'],
            mean_hr=row['mean_hr'],
            rmssd=row['rmssd'],
            pnn50=row['pnn50'],
            vlf=row['vlf'],
            lf=row['lf'],
            hf=row['hf'],
            lf_nu=row['lf_nu'],
            hf_nu=row['hf_nu']
        )
    
    # Generate visualizations and analysis
    hrv_analysis.visualize_comprehensive_hrv()
    status = hrv_analysis.analyze_hrv_status()
    print("\nHRV Status Analysis:")
    for key, value in status.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()