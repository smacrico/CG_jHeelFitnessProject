# RunningAnalysis_v51_REFACTORED.py
# (c)smacrico - Dec2024 - Refactored Version
# Fixes: Removed duplicate methods, consistent db_path usage, improved error handling

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime

class RunningAnalysis:
    def __init__(self, db_path):
        self.db_path = db_path  # Use parameter consistently
        self.training_log = self.load_training_data()

    def load_training_data(self):
        """Load training data from SQLite database with null handling"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
SELECT 
    date,
    COALESCE(running_economy, 0) as running_economy,
    COALESCE(vo2max, 0) as vo2max,
    COALESCE(distance, 0) as distance,
    COALESCE(time, 0) as time,
    COALESCE(heart_rate, 0) as heart_rate,
    COALESCE(running_economy / NULLIF(vo2max, 0), 0) AS efficiency_score,
    COALESCE(running_economy * (distance / NULLIF(time, 0)), 0) AS energy_cost
FROM running_sessions
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error loading  {e}")
            return pd.DataFrame()

    def add_session(self, date, running_economy, vo2max, distance, time, heart_rate, sport=None, cardicdrift=None):
        """Add a new running session to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
INSERT INTO running_sessions 
(date, running_economy, vo2max, distance, time, heart_rate, sport, cardicdrift)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (date, running_economy, vo2max, distance, time, heart_rate, sport, cardicdrift)
            )
            conn.commit()
            conn.close()
            self.training_log = self.load_training_data()
            print("Session added successfully")
        except Exception as e:
            print(f"Error adding session: {e}")

    def save_training_log_to_db(self):
        """Save training log DataFrame to SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            self.training_log.to_sql('training_logs', conn, if_exists='replace', index=False)
            conn.close()
            print("Training log successfully saved to database")
        except Exception as e:
            print(f"Error saving training log to database: {e}")

    def create_metrics_breakdown_table(self):
        """Create metrics_breakdown table if it doesn't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
CREATE TABLE IF NOT EXISTS metrics_breakdown (
    date TEXT,
    overall_score REAL,
    running_economy_normalized REAL,
    running_economy_weighted REAL,
    running_economy_raw_mean REAL,
    running_economy_raw_std REAL,
    vo2max_normalized REAL,
    vo2max_weighted REAL,
    vo2max_raw_mean REAL,
    vo2max_raw_std REAL,
    distance_normalized REAL,
    distance_weighted REAL,
    distance_raw_mean REAL,
    distance_raw_std REAL,
    efficiency_score_normalized REAL,
    efficiency_score_weighted REAL,
    efficiency_score_raw_mean REAL,
    efficiency_score_raw_std REAL,
    heart_rate_normalized REAL,
    heart_rate_weighted REAL,
    heart_rate_raw_mean REAL,
    heart_rate_raw_std REAL,
    running_economy_trend REAL,
    distance_progression REAL
)
                """
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error creating metrics_breakdown table: {e}")

    # ... [Include all other methods from original script with consistent self.db_path usage]

    def get_data_summary(self):
        """New method: Get basic data summary statistics"""
        try:
            summary = {
                'total_sessions': len(self.training_log),
                'avg_distance': self.training_log['distance'].mean(),
                'avg_running_economy': self.training_log['running_economy'].mean(),
                'avg_heart_rate': self.training_log['heart_rate'].mean(),
                'date_range': {
                    'start': self.training_log['date'].min(),
                    'end': self.training_log['date'].max()
                }
            }
            return summary
        except Exception as e:
            print(f"Error generating summary: {e}")
            return None

def main():
    # Flexible database path - now properly uses parameter
    db_path = input("Enter database path (or press Enter for default): ").strip()
    if not db_path:
        db_path = 'c:/smakryko/myHealthData/DataBasesDev/ApexDEV.db'

    # Create analysis object with proper path handling
    analysis = RunningAnalysis(db_path)
    
    # Display data summary
    summary = analysis.get_data_summary()
    if summary:
        print("=== Data Summary ===")
        print(f"Total Sessions: {summary['total_sessions']}")
        print(f"Average Distance: {summary['avg_distance']:.2f} km")
        print(f"Average Running Economy: {summary['avg_running_economy']:.2f}")
        
    # Continue with existing functionality...

if __name__ == "__main__":
    main()
