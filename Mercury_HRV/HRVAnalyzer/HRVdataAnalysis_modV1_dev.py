import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import sqlite3

class EnhancedHRVAnalysis:
    def __init__(self):
        self.hrv_log = None
        self.db_path = 'e:/jheel_dev/DataBasesDev/artemis_hrv.db'
        self.load_data_from_db()
    
    def load_data_from_db(self):
        """Fetch HRV data from the SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT 
                    date,
                    sd1,
                    sd2,
                    sdnn,
                    mean_rr,
                    mean_hr,
                    hrv_rmssd,
                    pnn50,
                    vlf,
                    lf,
                    hf,
                    lf_nu,
                    hf_nu
                FROM hrv_sessionsFBB
                ORDER BY date
            """
            
            self.hrv_log = pd.read_sql_query(query, conn)
            
            # Calculate derived metrics
            self.hrv_log['sd2_sd1_ratio'] = self.hrv_log['sd2'] / self.hrv_log['sd1']
            self.hrv_log['lf_hf_ratio'] = self.hrv_log['lf'] / self.hrv_log['hf']
            
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def visualize_comprehensive_hrv(self):
        """Generate comprehensive HRV visualizations"""
        if self.hrv_log is None or self.hrv_log.empty:
            print("No data available for visualization")
            return
            
        # Use a built-in style that's guaranteed to work
        # plt.style.use('default')
        plt.style.use('seaborn-v0_8-darkgrid')  # or any other valid seaborn styleplt.style.use('seaborn-v0_8-darkgrid')  # or any other valid seaborn style
        
        # Create figure with adjusted size
        fig = plt.figure(figsize=(20, 15))
        
        # Plot 1: Poincaré Plot Indices
        plt.subplot(3, 2, 1)
        plt.plot(self.hrv_log['date'], self.hrv_log['sd1'], 'b-o', label='SD1', markersize=4)
        plt.plot(self.hrv_log['date'], self.hrv_log['sd2'], 'r-o', label='SD2', markersize=4)
        plt.title('Poincaré Plot Indices Over Time', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 2: Frequency Domain Measures
        plt.subplot(3, 2, 2)
        plt.plot(self.hrv_log['date'], self.hrv_log['vlf'], 'g-o', label='VLF', markersize=4)
        plt.plot(self.hrv_log['date'], self.hrv_log['lf'], 'b-o', label='LF', markersize=4)
        plt.plot(self.hrv_log['date'], self.hrv_log['hf'], 'r-o', label='HF', markersize=4)
        plt.title('Frequency Domain Measures', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 3: Autonomic Balance
        plt.subplot(3, 2, 3)
        plt.plot(self.hrv_log['date'], self.hrv_log['lf_hf_ratio'], 'purple', marker='o', markersize=4)
        plt.title('LF/HF Ratio (Autonomic Balance)', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # Plot 4: Normalized Units
        plt.subplot(3, 2, 4)
        plt.plot(self.hrv_log['date'], self.hrv_log['lf_nu'], 'b-o', label='LF (n.u.)', markersize=4)
        plt.plot(self.hrv_log['date'], self.hrv_log['hf_nu'], 'r-o', label='HF (n.u.)', markersize=4)
        plt.title('Normalized Units of LF and HF', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 5: Time Domain Measures
        plt.subplot(3, 2, 5)
        plt.plot(self.hrv_log['date'], self.hrv_log['hrv_rmssd'], 'g-o', label='RMSSD', markersize=4)
        plt.plot(self.hrv_log['date'], self.hrv_log['sdnn'], 'b-o', label='SDNN', markersize=4)
        plt.title('Time Domain Measures', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 6: Heart Rate and RR Intervals
        ax1 = plt.subplot(3, 2, 6)
        ax2 = ax1.twinx()
        line1 = ax1.plot(self.hrv_log['date'], self.hrv_log['mean_hr'], 'b-o', 
                        label='Mean HR', markersize=4)
        line2 = ax2.plot(self.hrv_log['date'], self.hrv_log['mean_rr'], 'r-o', 
                        label='Mean RR', markersize=4)
        plt.title('Heart Rate and RR Intervals', fontsize=12)
        plt.xticks(rotation=45)
        
        # Add legend for the dual-axis plot
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels)
        plt.grid(True, alpha=0.3)
        
        # Adjust layout and display
        plt.tight_layout(pad=3.0)
        
        # Add a main title to the figure
        fig.suptitle('HRV Analysis Overview', fontsize=16, y=1.02)
        
        try:
            plt.show()
        except Exception as e:
            print(f"Error displaying plot: {e}")
            
            
    def analyze_hrv_status(self):
        """Analyze the latest HRV measurements"""
        if self.hrv_log is None or self.hrv_log.empty:
            return {"Error": "No data available for analysis"}
            
        latest = self.hrv_log.iloc[-1]
        
        # Handle potential NULL/None values with safe comparisons
        analysis = {
            'Autonomic Balance': 'Balanced' if (
                latest['lf_hf_ratio'] is not None and 
                0.5 <= latest['lf_hf_ratio'] <= 2
            ) else 'Sympathetic Dominant' if (
                latest['lf_hf_ratio'] is not None and 
                latest['lf_hf_ratio'] > 2
            ) else 'Parasympathetic Dominant',
            
            'Stress Level': 'Normal' if (
                latest['sd2_sd1_ratio'] is not None and 
                latest['sd2_sd1_ratio'] < 4
            ) else 'Elevated',
            
            'Recovery Status': 'Good' if (
                latest['hrv_rmssd'] is not None and 
                latest['hrv_rmssd'] > 20
            ) else 'Needs Improvement'
        }
        
        return analysis

    def generate_summary_stats(self):
        """Generate summary statistics for all HRV metrics"""
        if self.hrv_log is None or self.hrv_log.empty:
            return {"Error": "No data available for statistics"}
            
        summary_stats = self.hrv_log.describe()
        return summary_stats

def main():
    # Create analysis instance
    hrv_analysis = EnhancedHRVAnalysis()
    
    # Print the latest record values for debugging
    if hrv_analysis.hrv_log is not None and not hrv_analysis.hrv_log.empty:
        latest = hrv_analysis.hrv_log.iloc[-1]
        print("\nLatest record values:")
        for column in latest.index:
            print(f"{column}: {latest[column]}")
    
    # Generate and print HRV status analysis
    status = hrv_analysis.analyze_hrv_status()
    print("\nHRV Status Analysis:")
    for key, value in status.items():
        print(f"{key}: {value}")
    
    # Generate and print summary statistics
    print("\nSummary Statistics:")
    print(hrv_analysis.generate_summary_stats())
    
    # Generate visualizations
    hrv_analysis.visualize_comprehensive_hrv()

if __name__ == "__main__":
    main()