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
            # conn = sqlite3.connect(self.db_path)
            conn = sqlite3.connect(r'e:/jheel_dev/DataBasesDev/RunningAnalysis.db')
            query = """
            SELECT date, running_economy, vo2max, distance, 
                   time, 
                   heart_rate,
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
    
    def add_session(self, date, running_economy, vo2max, distance, time, heart_rate, sport=None, cardicdrift=None):
        """Add a new running session to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO running_sessions 
            (date, running_economy, vo2max, distance, time, heart_rate, sport, cardicdrift)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date, running_economy, vo2max, distance, time, heart_rate, sport, cardicdrift))
            
            conn.commit()
            conn.close()
            
            self.training_log = self.load_training_data()
            print(self.training_log)
        except Exception as e:
            print(f"Error adding session: {e}")
        
    def save_training_log_to_db(self):
        """Save training log DataFrame to SQLite database"""
        try:
            conn = sqlite3.connect(r'e:/jheel_dev/DataBasesDev/RunningAnalysis.db')
            
            # Create a new table for training logs if it doesn't exist
            self.training_log.to_sql('training_logs', 
                                    conn, 
                                    if_exists='replace',  # 'replace' will overwrite existing table
                                    index=False)
            
            conn.close()
            print("Training log successfully saved to database")
        except Exception as e:
            print(f"Error saving training log to database: {e}")

    def load_training_data(self):
        try:
            conn = sqlite3.connect(r'e:/jheel_dev/DataBasesDev/RunningAnalysis.db')
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
            print(f"Error loading data: {e}")
            return pd.DataFrame()
        
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
        
       # In the advanced_visualizations method, modify the pie chart section:

        # 4. Training Zones Pie Chart
        plt.subplot(2, 3, 4)
        try:
            # Calculate zones only for rows with valid running_economy and vo2max
            valid_rows = self.training_log[
                (self.training_log['running_economy'].notna()) & 
                (self.training_log['vo2max'].notna())
            ]
            
            if not valid_rows.empty:
                # Use the first valid row for zone calculation
                first_valid = valid_rows.iloc[0]
                zones = self.calculate_training_zones(first_valid['running_economy'], first_valid['vo2max'])
                
                zone_durations = {}
                for zone, (lower, upper) in zones.items():
                    count = len(valid_rows[
                        (valid_rows['running_economy'] >= lower) & 
                        (valid_rows['running_economy'] < upper)
                    ])
                    if count > 0:  # Only include zones with data
                        zone_durations[zone] = count
                
                if zone_durations:  # Check if we have any data to plot
                    plt.pie(
                        list(zone_durations.values()), 
                        labels=list(zone_durations.keys()), 
                        autopct='%1.1f%%'
                    )
                    plt.title('Training Zones Distribution')
                else:
                    plt.text(0.5, 0.5, 'No valid zone data', ha='center', va='center')
            else:
                plt.text(0.5, 0.5, 'No valid training data', ha='center', va='center')
        except Exception as e:
            print(f"Error creating pie chart: {e}")
            plt.text(0.5, 0.5, 'Error creating pie chart', ha='center', va='center')
        
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
        
        
    # trainning score calculation

    def calculate_training_score(self):
        """
        Calculate a comprehensive training score based on multiple performance metrics
        
        Returns a dictionary with detailed score breakdown and overall training score
        """
        # Normalize and weight different metrics
        try:
            # Normalize each metric
            normalized_data = self.training_log.copy()
            
            # Metrics to consider
            metrics = {
                'running_economy': {'weight': 0.25, 'higher_is_better': True},
                'vo2max': {'weight': 0.20, 'higher_is_better': True},
                'distance': {'weight': 0.15, 'higher_is_better': True},
                'efficiency_score': {'weight': 0.20, 'higher_is_better': True},
                'heart_rate': {'weight': 0.20, 'higher_is_better': False}
            }
            
            # Normalization function
            def normalize_metric(series, higher_is_better):
                if higher_is_better:
                    return (series - series.min()) / (series.max() - series.min())
                else:
                    return 1 - ((series - series.min()) / (series.max() - series.min()))
            
            # Calculate normalized scores
            normalized_scores = {}
            for metric, config in metrics.items():
                normalized_scores[metric] = normalize_metric(
                    normalized_data[metric], 
                    config['higher_is_better']
                )
            
            # Calculate weighted scores
            weighted_scores = {}
            for metric, config in metrics.items():
                weighted_scores[metric] = normalized_scores[metric] * config['weight']
            
            # Overall training score
            # overall_score = sum(weighted_scores.values()) * 100
            # Overall training score
            overall_score = sum(weighted_scores[metric].mean() for metric in metrics) * 100
            
            # Detailed analysis
            analysis = {
                'overall_score': overall_score,
                'metric_breakdown': {
                    metric: {
                        'normalized_value': normalized_scores[metric].mean(),
                        'weighted_value': weighted_scores[metric].mean(),
                        'raw_mean': self.training_log[metric].mean(),
                        'raw_std': self.training_log[metric].std()
                    } for metric in metrics
                },
                'performance_trends': {
                    'running_economy_trend': normalized_scores['running_economy'].corr(normalized_data['date']),
                    'distance_progression': normalized_scores['distance'].corr(normalized_data['date'])
                }
            }
            
            return analysis
        
        except Exception as e:
            print(f"Error calculating training score: {e}")
            return None 

def main():
    # Database path
    db_path = 'e:/jheel_dev/DataBasesDev/running_analysis.db'

    # Create analysis object
    analysis = RunningAnalysis('e:/jheel_dev/DataBasesDev/running_analysis.db')
    
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
    
    
    # Save training log to database.
    analysis.save_training_log_to_db()
    
    # Print training log
    print("Training Log:")
    print(analysis.training_log)
    
    # Visualize trends
    analysis.visualize_trends()
    
    # Visualize advanced metrics
    analysis.advanced_visualizations()
    
    # Calculate and print training score
    training_score = analysis.calculate_training_score()
    if training_score:
        print("\nTraining Score Analysis:")
        print(f"Overall Training Score: {float(training_score['overall_score']):.2f}")
        # print(f"Overall Training Score: {training_score['overall_score']}")
        
        print("\nMetric Breakdown:")
        for metric, details in training_score['metric_breakdown'].items():
            print(f"{metric.replace('_', ' ').title()}:")
            print(f"  Normalized Value: {details['normalized_value']}")
            print(f"  Weighted Value: {details['weighted_value']}")
            print(f"  Raw Mean: {details['raw_mean']}")
            print(f"  Raw Std Dev: {details['raw_std']}")
        
        print("\nPerformance Trends:")
        for trend, value in training_score['performance_trends'].items():
            print(f"{trend.replace('_', ' ').title()}: {value}")

    
    
if __name__ == "__main__":
    
    main()