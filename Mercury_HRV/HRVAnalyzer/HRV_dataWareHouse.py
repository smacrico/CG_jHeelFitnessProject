import sqlite3
import os
import logging
import datetime
import pandas as pd
import numpy as np
from fitparse import FitFile

# --- Configuration ---

# --- DB Name and Log Path --- "Mercury_DWH-HRV.db"
DB_PATH = "c:/smakryko/myHealthData/DataBasesDev/Mercury_DWH-HRV.db"
LOG_PATH = "c:/temp/logsDWH/hrv_unified.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Unified Table Definitions ---
def create_unified_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Unified sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hrv_sessions (
        activity_id TEXT PRIMARY KEY,
        source TEXT,
        timestamp TEXT,
        sport TEXT,
        min_hr INTEGER,
        hrv_rmssd REAL,
        hrv_sdrr_f REAL,
        hrv_sdrr_l REAL,
        hrv_pnn50 REAL,
        hrv_pnn20 REAL,
        armssd REAL,
        asdnn REAL,
        SaO2 REAL,
        trnd_hrv REAL,
        recovery REAL,
        sdnn REAL,
        sdsd REAL,
        dBeats INTEGER,
        sBeats INTEGER,
        session_hrv REAL,
        NN50 INTEGER,
        NN20 INTEGER,
        sd1 REAL,
        sd2 REAL,
        lf REAL,
        hf REAL,
        vlf REAL,
        pNN50 REAL,
        lf_nu REAL,
        hf_nu REAL,
        mean_hr REAL,
        mean_rr REAL,
        stress_hrpa REAL,
        steps INTEGER,
        distance REAL,
        vo2max REAL
    )
    ''')

    # Unified records table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hrv_records (
        activity_id TEXT,
        record INTEGER,
        source TEXT,
        timestamp TEXT,
        hrv_s REAL,
        hrv_btb REAL,
        hrv_hr REAL,
        rrhr REAL,
        rawHR REAL,
        RRint REAL,
        hrv REAL,
        rmssd REAL,
        sdnn REAL,
        SaO2_C REAL,
        stress_hrp REAL,
        PRIMARY KEY (activity_id, record)
    )
    ''')

    conn.commit()
    conn.close()
    logging.info("Unified tables created.")

# --- Data Ingestion ---
def ingest_fit_file(file_path, source_hint=None):
    fit_file = FitFile(file_path)
    activity_id = os.path.splitext(os.path.basename(file_path))[0].split('_')[0]
    source = source_hint or "UNKNOWN"
    session_inserted = False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    record_num = 0

    for msg in fit_file.messages:
        if msg.name == 'record':
            fields = {field.name: field.value for field in msg.fields}
            cursor.execute('''
                INSERT OR IGNORE INTO hrv_records (
                    activity_id, record, source, timestamp, hrv_s, hrv_btb, hrv_hr, rrhr,
                    rawHR, RRint, hrv, rmssd, sdnn, SaO2_C, stress_hrp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity_id,
                record_num,
                source,
                fields.get('timestamp'),
                fields.get('hrv_s'),
                fields.get('hrv_btb'),
                fields.get('hrv_hr'),
                fields.get('rrhr'),
                fields.get('rawHR'),
                fields.get('RRint'),
                fields.get('hrv'),
                fields.get('rmssd'),
                fields.get('SDNN'),
                fields.get('SaO2_C'),
                fields.get('stress_hrp')
            ))
            record_num += 1

        elif msg.name == 'session' and not session_inserted:
            fields = {field.name: field.value for field in msg.fields}
            cursor.execute('''
                INSERT OR IGNORE INTO hrv_sessions (
                    activity_id, source, timestamp, sport, min_hr, hrv_rmssd, hrv_sdrr_f,
                    hrv_sdrr_l, hrv_pnn50, hrv_pnn20, armssd, asdnn, SaO2, trnd_hrv, recovery,
                    sdnn, sdsd, dBeats, sBeats, session_hrv, NN50, NN20, sd1, sd2, lf, hf, vlf,
                    pNN50, lf_nu, hf_nu, mean_hr, mean_rr, stress_hrpa, steps, distance, vo2max
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity_id,
                source,
                fields.get('timestamp'),
                fields.get('sport'),
                fields.get('min_hr'),
                fields.get('hrv_rmssd'),
                fields.get('hrv_sdrr_f'),
                fields.get('hrv_sdrr_l'),
                fields.get('hrv_pnn50'),
                fields.get('hrv_pnn20'),
                fields.get('armssd'),
                fields.get('asdnn'),
                fields.get('SaO2'),
                fields.get('trnd_hrv'),
                fields.get('recovery'),
                fields.get('SDNN'),
                fields.get('SDSD'),
                fields.get('dBeats'),
                fields.get('sBeats'),
                fields.get('session_hrv'),
                fields.get('NN50'),
                fields.get('NN20'),
                fields.get('SD1'),
                fields.get('SD2'),
                fields.get('LF'),
                fields.get('HF'),
                fields.get('VLF'),
                fields.get('pNN50'),
                fields.get('LFnu'),
                fields.get('HFnu'),
                fields.get('Mean HR'),
                fields.get('Mean RR'),
                fields.get('stress_hrpa'),
                fields.get('steps'),
                fields.get('total_distance'),
                fields.get('VO2maxSession')
            ))
            session_inserted = True

    conn.commit()
    conn.close()
    logging.info(f"Ingested file: {file_path}")

def ingest_folder(folder_path, source_hint=None):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.fit'):
            try:
                ingest_fit_file(os.path.join(folder_path, filename), source_hint)
            except Exception as e:
                logging.error(f"Failed to ingest {filename}: {e}")


# --- HRV Data Analysis ---
# --- ################# ---
# --- Analytics -----------
# --- ################# ---
# --- HRV Trends Analysis ---
def analyze_hrv_trends(days=30):
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT date(timestamp) as date, AVG(hrv_rmssd) as avg_rmssd, AVG(sdnn) as avg_sdnn
    FROM hrv_sessions
    WHERE timestamp >= date('now', ?)
    GROUP BY date(timestamp)
    ORDER BY date(timestamp) DESC
    """
    df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
    conn.close()
    if df.empty:
        print("No HRV data found for analysis.")
        return
    print(df)
    # Trend calculation (simple linear regression)
    if len(df) > 1:
        x = np.arange(len(df))
        rmssd_trend = np.polyfit(x, df['avg_rmssd'], 1)[0]
        print(f"RMSSD trend (per day): {rmssd_trend:.2f}")
    else:
        print("Not enough data for trend analysis.")


# --- Recovery Score Calculation ---

def calculate_recovery_score(activity_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT hrv_rmssd, sdnn, hrv_pnn50 FROM hrv_sessions WHERE activity_id = ?
    """, (activity_id,))
    result = cursor.fetchone()
    conn.close()
    if result and all(result):
        rmssd_score = min(100, result[0] / 2)
        sdnn_score = min(100, result[1] / 2)
        pnn50_score = result[2] or 0
        recovery_score = (rmssd_score + sdnn_score + pnn50_score) / 3
        print(f"Recovery score for {activity_id}: {recovery_score:.2f}")
        return recovery_score
    else:
        print(f"No session data found for {activity_id}")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    create_unified_tables()
    # Example: ingest all .fit files from a folder
    ingest_folder("C:/smakryko/myHealthData/HealtDataSystemAnalysis/TestFitFiles/Garmin", source_hint="GARMIN")
    # Run analytics
    analyze_hrv_trends(days=30)
    # Example recovery score
    # calculate_recovery_score("your_activity_id_here")
