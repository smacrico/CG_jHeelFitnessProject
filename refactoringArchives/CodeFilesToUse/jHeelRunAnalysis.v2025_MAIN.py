import pandas as pd
import sqlite3
import rarfile
import os

def create_database():
    conn = sqlite3.connect('RunAnalysis.db')
    cursor = conn.cursor()
    
    # Create run_sessions table with fields from your sample data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS run_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER,
        start_time INTEGER,
        start_position_lat INTEGER,
        start_position_long INTEGER,
        total_elapsed_time FLOAT,
        total_timer_time FLOAT,
        total_distance FLOAT,
        total_cycles INTEGER,
        nec_lat INTEGER,
        nec_long INTEGER,
        swc_lat INTEGER,
        swc_long INTEGER,
        total_calories INTEGER,
        avg_speed FLOAT,
        max_speed FLOAT,
        total_ascent INTEGER,
        total_descent INTEGER,
        avg_heart_rate INTEGER,
        max_heart_rate INTEGER,
        avg_cadence INTEGER,
        max_cadence INTEGER,
        total_training_effect FLOAT,
        avg_temperature FLOAT,
        max_temperature FLOAT,
        vo2max_session INTEGER,
        vo2max_smooth FLOAT,
        cardiac_drift FLOAT,
        aerobic_efficiency FLOAT,
        running_economy FLOAT
    )
    ''')
    
    # Create run_records table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS run_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        timestamp INTEGER,
        distance FLOAT,
        speed FLOAT,
        heart_rate INTEGER,
        cadence INTEGER,
        altitude FLOAT,
        temperature FLOAT,
        FOREIGN KEY (session_id) REFERENCES run_sessions(id)
    )
    ''')
    
    conn.commit()
    return conn

def extract_csv_from_rar(rar_filename):
    rar = rarfile.RarFile(rar_filename)
    extracted_files = []
    
    for f in rar.namelist():
        if f.endswith('.csv'):
            rar.extract(f)
            extracted_files.append(f)
            
    return extracted_files

def process_session_data(filename):
    df = pd.read_csv(filename)
    # Ensure we're only processing one row
    if len(df) > 0:
        return df.iloc[0]
    return None

def process_record_data(filename):
    return pd.read_csv(filename)

def store_session(conn, session_data):
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO run_sessions (
        timestamp, start_time, start_position_lat, start_position_long,
        total_elapsed_time, total_timer_time, total_distance, total_cycles,
        nec_lat, nec_long, swc_lat, swc_long, total_calories,
        avg_speed, max_speed, total_ascent, total_descent,
        avg_heart_rate, max_heart_rate, avg_cadence, max_cadence,
        total_training_effect, avg_temperature, max_temperature,
        vo2max_session, vo2max_smooth, cardiac_drift, aerobic_efficiency,
        running_economy
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_data.get('timestamp'),
        session_data.get('start_time'),
        session_data.get('start_position_lat'),
        session_data.get('start_position_long'),
        session_data.get('total_elapsed_time'),
        session_data.get('total_timer_time'),
        session_data.get('total_distance'),
        session_data.get('total_cycles'),
        session_data.get('nec_lat'),
        session_data.get('nec_long'),
        session_data.get('swc_lat'),
        session_data.get('swc_long'),
        session_data.get('total_calories'),
        session_data.get('avg_speed'),
        session_data.get('max_speed'),
        session_data.get('total_ascent'),
        session_data.get('total_descent'),
        session_data.get('avg_heart_rate'),
        session_data.get('max_heart_rate'),
        session_data.get('avg_cadence'),
        session_data.get('max_cadence'),
        session_data.get('total_training_effect'),
        session_data.get('avg_temperature'),
        session_data.get('max_temperature'),
        session_data.get('VO2maxSession'),
        session_data.get('VO2maxSmooth'),
        session_data.get('CardiacDrift'),
        session_data.get('Aerobic Efficiency'),
        session_data.get('Running Economy')
    ))
    
    conn.commit()
    return cursor.lastrowid

def store_records(conn, records_df, session_id):
    cursor = conn.cursor()
    
    for _, record in records_df.iterrows():
        cursor.execute('''
        INSERT INTO run_records (
            session_id, timestamp, distance, speed,
            heart_rate, cadence, altitude, temperature
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            record.get('timestamp'),
            record.get('distance'),
            record.get('speed'),
            record.get('heart_rate'),
            record.get('cadence'),
            record.get('altitude'),
            record.get('temperature')
        ))
    
    conn.commit()

def main():
    conn = create_database()
    
    try:
        # Extract files from RAR
        session_file = "128408-118657300_session_1.csv"
        record_file = "128408-118657300_record_2.csv"
        
        # Process session data
        session_data = process_session_data(session_file)
        if session_data is not None:
            # Store session and get session_id
            session_id = store_session(conn, session_data)
            
            # Process and store record data
            records_df = process_record_data(record_file)
            store_records(conn, records_df, session_id)
            
            print("Data successfully stored in database")
        else:
            print("No session data found")
            
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()