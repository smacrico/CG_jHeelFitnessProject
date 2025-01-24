# code refactor to use data from SQLi Database
# (c)smacrico - Dec2024

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime

class RunningAnalysis:
    def __init__(self, db_path):
        self.db_path = db_path
        self.training_log = self.load_training_data()
    
    def load_training_data(self):
        """Load training data from SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT date, running_economy, vo2max, distance, 
                   time, heart_rate,
                   running_economy / vo2max AS efficiency_score,
                   running_economy * (distance / time) AS energy_cost
            FROM running_sessions
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def add_session(self, date, running_economy, vo2max, distance, time, heart_rate):
        """Add a new running session to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS running_sessions (
                date TEXT,
                running_economy REAL,
                vo2max REAL,
                distance REAL,
                time REAL,
                heart_rate REAL
            )
            ''')
            
            # Insert new session
            cursor.execute('''
            INSERT INTO running_sessions 
            (date, running_economy, vo2max, distance, time, heart_rate)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (date, running_economy, vo2max, distance, time, heart_rate))
            
            conn.commit()
            conn.close()
            
            # Reload training log
            self.training_log = self.load_training_data()
        except Exception as e:
            print(f"Error adding session: {e}")
    
    def visualize_trends(self):
        """Create visualizations of running data"""
        try:
            plt.figure(figsize=(15, 10))
            
            # Convert date to datetime
            self.training_log['date'] = pd.to_datetime(self.training_log['date'])
            
            # Plot 1: Running Economy over time
            plt.subplot(2, 2, 1)
            plt.plot(self.training_log['date'], self.training_log['running_economy'], 'b-o')
            plt.title('Running Economy Trend')
            plt.xticks(rotation=45)
            plt.ylabel('Running Economy')
            
            # Plot 2: Efficiency Score over time
            plt.subplot(2, 2, 2)
            plt.plot(self.training_log['date'], self.training_log['efficiency_score'], 'g-o')
            plt.title('Efficiency Score Trend')
            plt.xticks(rotation=45)
            plt.ylabel('Efficiency Score')
            
            # Plot 3: Energy Cost vs Distance
            plt.subplot(2, 2, 3)
            plt.scatter(self.training_log['distance'], self.training_log['energy_cost'])
            plt.title('Energy Cost vs Distance')
            plt.xlabel('Distance (km)')
            plt.ylabel('Energy Cost')
            
            # Plot 4: Heart Rate vs Running Economy
            plt.subplot(2, 2, 4)
            plt.scatter(self.training_log['heart_rate'], self.training_log['running_economy'])
            plt.title('Heart Rate vs Running Economy')
            plt.xlabel('Heart Rate (bpm)')
            plt.ylabel('Running Economy')
            
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print(f"Visualization error: {e}")
    
    def calculate_training_zones(self, running_economy, vo2max):
        """Calculate training zones based on running economy"""
        zones = {
            'Recovery': (0.6 * running_economy, 0.7 * running_economy),
            'Endurance': (0.7 * running_economy, 0.8 * running_economy),
            'Tempo': (0.8 * running_economy, 0.9 * running_economy),
            'Threshold': (0.9 * running_economy, running_economy),
            'VO2Max': (running_economy, 1.1 * running_economy)
        }
        return zones
    
    def print_training_zones(self, running_economy, vo2max):
        """Print training zones"""
        training_zones = self.calculate_training_zones(running_economy, vo2max)
        print("\nTraining Zones based on Running Economy:")
        for zone, (lower, upper) in training_zones.items():
            print(f"{zone}: {lower:.1f} - {upper:.1f}")

def main():
    # Database path
    db_path = 'e:/jheel_dev/DataBasesDev/running_analysis.db'

    # Create analysis object
    analysis = RunningAnalysis(db_path)
    
    # Add sample session if database is empty
    if analysis.training_log.empty:
        analysis.add_session(
            date=datetime.now().strftime('%Y-%m-%d'),
            running_economy=73,
            vo2max=19.0,
            distance=5,
            time=27,
            heart_rate=150
        )
    
    # Print training log
    print("Training Log:")
    print(analysis.training_log)
    
    # Visualize trends
    analysis.visualize_trends()
    
    # Print training zones using first row data
    first_row = analysis.training_log.iloc[0]
    analysis.print_training_zones(
        first_row['running_economy'], 
        first_row['vo2max']
    )

if __name__ == "__main__":
    main()