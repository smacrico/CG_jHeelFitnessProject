import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import sqlite3

class EnhancedHRVAnalysis:
    def __init__(self):
        self.hrv_log = None
        self.db_path = 'e:/jheel_dev/DataBasesDev/artemis_hrv.db'
        self.create_analysis_tables()
        self.load_data_from_db()
    
    def create_analysis_tables(self):
        """Create tables for storing analysis results if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Drop existing tables if they exist
            cursor.execute('DROP TABLE IF EXISTS latest_hrv_recordsV2')
            cursor.execute('DROP TABLE IF EXISTS hrv_status_analysisV2')
            cursor.execute('DROP TABLE IF EXISTS hrv_summary_statsV2')
            
            # Create table for latest records with both numeric and text columns
            cursor.execute('''
                CREATE TABLE latest_hrv_recordsV2 (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT,
                    metric_value_num REAL,
                    metric_value_text TEXT
                )
            ''')
            
            # Create table for HRV status analysis
            cursor.execute('''
                CREATE TABLE hrv_status_analysisV2 (
                    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT,
                    status TEXT
                )
            ''')
            
            # Create table for summary statistics
            cursor.execute('''
                CREATE TABLE hrv_summary_statsV2 (
                    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT,
                    count REAL,
                    mean REAL,
                    std REAL,
                    min REAL,
                    q25 REAL,
                    median REAL,
                    q75 REAL,
                    max REAL
                )
            ''')
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
        finally:
            if conn:
                conn.close()

    def store_latest_record(self):
        """Store the latest HRV record values"""
        if self.hrv_log is None or self.hrv_log.empty:
            return
        
        latest = self.hrv_log.iloc[-1]
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First, let's modify the table structure to accommodate text values
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS latest_hrv_recordsV2 (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT,
                    metric_value_num REAL,
                    metric_value_text TEXT
                )
            ''')
            
            # Store each metric from the latest record
            for column in latest.index:
                if column != 'date':  # Skip date column
                    value = latest[column]
                    if pd.isna(value):
                        value_num = None
                        value_text = None
                    else:
                        try:
                            value_num = float(value)
                            value_text = None
                        except (ValueError, TypeError):
                            value_num = None
                            value_text = str(value)
                    
                    cursor.execute('''
                        INSERT INTO latest_hrv_recordsV2 
                        (timestamp, metric_name, metric_value_num, metric_value_text)
                        VALUES (?, ?, ?, ?)
                    ''', (current_time, column, value_num, value_text))
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error storing latest record: {e}")
        finally:
            if conn:
                conn.close()

    def store_hrv_status(self, status_dict):
        """Store HRV status analysis"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for metric, status in status_dict.items():
                cursor.execute('''
                    INSERT INTO hrv_status_analysisV2 (timestamp, metric_name, status)
                    VALUES (?, ?, ?)
                ''', (current_time, metric, status))
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error storing HRV status: {e}")
        finally:
            if conn:
                conn.close()

    def store_summary_stats(self):
        """Store summary statistics"""
        if self.hrv_log is None or self.hrv_log.empty:
            return
            
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        summary_stats = self.hrv_log.describe()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for column in summary_stats.columns:
                if column != 'date':  # Skip date column
                    cursor.execute('''
                        INSERT INTO hrv_summary_statsV2 
                        (timestamp, metric_name, count, mean, std, min, q25, median, q75, max)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        current_time,
                        column,
                        float(summary_stats[column]['count']),
                        float(summary_stats[column]['mean']),
                        float(summary_stats[column]['std']),
                        float(summary_stats[column]['min']),
                        float(summary_stats[column]['25%']),
                        float(summary_stats[column]['50%']),
                        float(summary_stats[column]['75%']),
                        float(summary_stats[column]['max'])
                    ))
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error storing summary statistics: {e}")
        finally:
            if conn:
                conn.close()
                
                
    def analyze_hrv_status(self):
        """Analyze the latest HRV measurements"""
        if self.hrv_log is None or self.hrv_log.empty:
            return {"Error": "No data available for analysis"}
            
        latest = self.hrv_log.iloc[-1]
        
        # Handle potential NULL/None values with safe comparisons
        analysis = {
            'Autonomic Balance': 'Balanced' if (
                'lf_hf_ratio' in latest and 
                latest['lf_hf_ratio'] is not None and 
                0.5 <= float(latest['lf_hf_ratio']) <= 2
            ) else 'Sympathetic Dominant' if (
                'lf_hf_ratio' in latest and 
                latest['lf_hf_ratio'] is not None and 
                float(latest['lf_hf_ratio']) > 2
            ) else 'Parasympathetic Dominant',
            
            'Stress Level': 'Normal' if (
                'sd2_sd1_ratio' in latest and 
                latest['sd2_sd1_ratio'] is not None and 
                float(latest['sd2_sd1_ratio']) < 4
            ) else 'Elevated',
            
            'Recovery Status': 'Good' if (
                'hrv_rmssd' in latest and 
                latest['hrv_rmssd'] is not None and 
                float(latest['hrv_rmssd']) > 20
            ) else 'Needs Improvement'
        }
        
        return analysis
    def load_data_from_db(self):
        """Fetch HRV data from the SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT * FROM hrv_sessionsFBB ORDER BY date"
            self.hrv_log = pd.read_sql_query(query, conn)
            
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
        finally:
            if conn:
                conn.close()

def main():
    # Create analysis instance
    hrv_analysis = EnhancedHRVAnalysis()
    
    # Store latest record values
    hrv_analysis.store_latest_record()
    
    # Generate and store HRV status analysis
    status = hrv_analysis.analyze_hrv_status()
    hrv_analysis.store_hrv_status(status)
    
    # Store summary statistics
    hrv_analysis.store_summary_stats()
    
    print("Analysis results have been stored in the database.")

if __name__ == "__main__":
    main()