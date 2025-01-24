import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
from datetime import datetime

class HRVAnalysis:
    def __init__(self, db_path='e:/jheel_dev/DataBasesDev/artemis_hrv.db'):
        self.db_path = db_path
        self.hrv_log = self._load_data_from_database()
    
    def _load_data_from_database(self):
        """Load HRV data from SQLite database"""
        try:
            conn = sqlite3.connect(r'e:/jheel_dev/DataBasesDev/artemis_hrv.db')
            query = """
            SELECT 
                date, hrv, pnn50, pnn20, rmssd, sdnn, 
                hrv_diff_from_avg, oxygen_saturation, 
                average_hrv, recovery_score 
            FROM hrv_sessionsDEV
            ORDER BY date
            """
            hrv_log = pd.read_sql_query(query, conn)
            conn.close()
            return hrv_log
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return pd.DataFrame(columns=[
                'date', 'hrv', 'pnn50', 'pnn20', 'rmssd', 'sdnn',
                'hrv_diff_from_avg', 'oxygen_saturation',
                'average_hrv', 'recovery_score'
            ])
    
    def add_session(self, date, hrv, pnn50, pnn20, rmssd, sdnn,
                   hrv_diff_from_avg, oxygen_saturation, average_hrv, recovery_score):
        """Add a new HRV session to the database"""
        try:
            conn = sqlite3.connect(r'e:/jheel_dev/DataBasesDev/artemis_hrv.db')
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS hrv_sessionsDEV (
                date TEXT PRIMARY KEY,
                hrv REAL,
                pnn50 REAL,
                pnn20 REAL,
                rmssd REAL,
                sdnn REAL,
                hrv_diff_from_avg REAL,
                oxygen_saturation REAL,
                average_hrv REAL,
                recovery_score REAL
            )
            ''')
            
            # Insert or replace the session data
            cursor.execute('''
            INSERT OR REPLACE INTO hrv_sessionsDEV 
            (date, hrv, pnn50, pnn20, rmssd, sdnn, 
            hrv_diff_from_avg, oxygen_saturation, 
            average_hrv, recovery_score) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(date), hrv, pnn50, pnn20, rmssd, sdnn,
                hrv_diff_from_avg, oxygen_saturation, 
                average_hrv, recovery_score
            ))
            
            conn.commit()
            conn.close()
            
            # Reload the data
            self.hrv_log = self._load_data_from_database()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
    
    def visualize_hrv_metrics(self):
        # (Keep the existing visualization method)
        plt.style.use('seaborn')
        fig = plt.figure(figsize=(15, 12))
        
        # Convert date to datetime for proper plotting
        self.hrv_log['date'] = pd.to_datetime(self.hrv_log['date'])
        
        # Plot 1: HRV Trend with Average
        plt.subplot(2, 2, 1)
        plt.plot(self.hrv_log['date'], self.hrv_log['hrv'], 'b-o', label='HRV')
        plt.plot(self.hrv_log['date'], self.hrv_log['average_hrv'], 'r--', label='Average HRV')
        plt.title('HRV Trend Over Time')
        plt.xticks(rotation=45)
        plt.legend()
        
        # (Rest of the plotting code remains the same)
        
        plt.tight_layout()
        plt.show()
    
    def analyze_recovery_state(self, current_hrv, average_hrv):
        # (Existing method remains the same)
        hrv_diff = current_hrv - average_hrv
        if hrv_diff > 5:
            return "Well recovered"
        elif hrv_diff < -5:
            return "Need more recovery"
        else:
            return "Moderate recovery state"
        
        
    ####################################
    ##### Recovery Score Calculation####
    ####################################
        
    def calculate_recovery_score(self, hrv, rmssd, pnn50):
        # Example calculation (this is a simplified model)
        # Normalize and weight different HRV metrics
        normalized_hrv = (hrv - self.hrv_log['hrv'].min()) / (self.hrv_log['hrv'].max() - self.hrv_log['hrv'].min())
        normalized_rmssd = (rmssd - self.hrv_log['rmssd'].min()) / (self.hrv_log['rmssd'].max() - self.hrv_log['rmssd'].min())
        normalized_pnn50 = (pnn50 - self.hrv_log['pnn50'].min()) / (self.hrv_log['pnn50'].max() - self.hrv_log['pnn50'].min())
        
        # Weighted combination (adjust weights as needed)
        recovery_score = (
            0.5 * normalized_hrv + 
            0.3 * normalized_rmssd + 
            0.2 * normalized_pnn50
        ) * 100  # Scale to 0-100
        
        return round(recovery_score, 2)    

# Example usage and main call fuction ####
def main():
    # Initialize analysis with database
    analysis = HRVAnalysis('e:/jheel_dev/DataBasesDev/artemis_hrv.db')
    
    # Add a new session
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
    
    # Generate visualizations
    analysis.visualize_hrv_metrics()
    
    # Calculate current recovery state
    current_state = analysis.analyze_recovery_state(43.81, 65.72)
    print(f"\nCurrent Recovery State: {current_state}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(analysis.hrv_log.describe())

if __name__ == '__main__':
    main()