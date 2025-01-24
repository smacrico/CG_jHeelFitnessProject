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
            
    def advanced_visualizations(self):
        """Create advanced performance visualizations"""
        plt.figure(figsize=(20, 15))
        
        # 1. Cumulative Distance Over Time
        plt.subplot(2, 3, 1)
        self.training_log['cumulative_distance'] = self.training_log['distance'].cumsum()
        plt.plot(self.training_log['date'], self.training_log['cumulative_distance'], 'b-o')
        plt.title('Cumulative Running Distance')
        plt.xlabel('Date')
        plt.ylabel('Total Distance (km)')
        plt.xticks(rotation=45)
        
        # 2. Moving Average of Running Economy
        plt.subplot(2, 3, 2)
        self.training_log['running_economy_ma'] = self.training_log['running_economy'].rolling(window=3).mean()
        plt.plot(self.training_log['date'], self.training_log['running_economy'], 'g-', label='Original')
        plt.plot(self.training_log['date'], self.training_log['running_economy_ma'], 'r-', label='3-Session Moving Avg')
        plt.title('Running Economy Trend')
        plt.xlabel('Date')
        plt.ylabel('Running Economy')
        plt.legend()
        plt.xticks(rotation=45)
        
        # 3. Heart Rate vs Pace Correlation
        plt.subplot(2, 3, 3)
        pace = self.training_log['time'] / self.training_log['distance']
        plt.scatter(pace, self.training_log['heart_rate'], alpha=0.7)
        plt.title('Pace vs Heart Rate')
        plt.xlabel('Pace (min/km)')
        plt.ylabel('Heart Rate (bpm)')
        
        # 4. Training Zones Pie Chart
        plt.subplot(2, 3, 4)
        zones = self.training_log.apply(
            lambda row: self.calculate_training_zones(row['running_economy'], row['vo2max']), 
            axis=1
        )
        zone_durations = {zone: len(self.training_log[
            (self.training_log['running_economy'] >= lower) & 
            (self.training_log['running_economy'] < upper)
        ]) for zone, (lower, upper) in zones.iloc[0].items()}
        
        plt.pie(zone_durations.values(), labels=zone_durations.keys(), autopct='%1.1f%%')
        plt.title('Training Zones Distribution')
        
        # 5. Performance Progression Radar Chart
        plt.subplot(2, 3, 5, polar=True)
        metrics = [
            'running_economy', 
            'vo2max', 
            'distance', 
            'efficiency_score', 
            'heart_rate'
        ]
        
        # Normalize metrics
        normalized_metrics = self.training_log[metrics].apply(
            lambda x: (x - x.min()) / (x.max() - x.min())
        )
        
        # Average of normalized metrics for each session
        avg_metrics = normalized_metrics.mean()
        
        # Radar chart
        angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False)
        values = avg_metrics.values
        values = np.concatenate((values, [values[0]]))  # Repeat first value to close the polygon
        angles = np.concatenate((angles, [angles[0]]))  # Repeat first angle
        
        plt.polar(angles, values, 'o-', linewidth=2)
        plt.fill(angles, values, alpha=0.25)
        plt.xticks(angles[:-1], metrics)
        plt.title('Performance Metrics Radar Chart')
        
        # 6. Seasonal Performance Heatmap
        plt.subplot(2, 3, 6)
        self.training_log['month'] = self.training_log['date'].dt.month
        seasonal_performance = self.training_log.groupby('month')['running_economy'].mean()
        
        plt.imshow([seasonal_performance.values], cmap='YlOrRd', aspect='auto')
        plt.colorbar(label='Avg Running Economy')
        plt.title('Seasonal Performance Heatmap')
        plt.xlabel('Month')
        plt.xticks(range(len(seasonal_performance)), seasonal_performance.index)
        
        plt.tight_layout()
        plt.show()

def main():
    # Database path
    db_path = 'e:/jheel_dev/DataBasesDev/running_analysis.db'

    # Create analysis object
    analysis = RunningAnalysis(db_path)
        
    # Call advanced visualizations
    # analysis.advanced_visualizations()

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
    
    # Visualize advanced metrics
    analysis.advanced_visualizations()
    
    # Print training zones using first row data
    first_row = analysis.training_log.iloc[0]
    analysis.print_training_zones(
        first_row['running_economy'], 
        first_row['vo2max']
    )

if __name__ == "__main__":
    
    main()