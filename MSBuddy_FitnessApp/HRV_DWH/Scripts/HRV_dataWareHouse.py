import sqlite3
import os
import logging
import datetime
import pandas as pd
import numpy as np
from fitparse import FitFile

# --- Configuration ---

# --- DB Name and Log Path --- "Mercury_DWH-HRV.db"
DB_PATH = "c:/smakrykoDBs/Mercury_DWH_HRV.db"
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
        name TEXT,
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
        name TEXT,
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


# -- Data Ingestion
def ingest_fit_file(file_path, source_hint=None):
    fit_file = FitFile(file_path)
    activity_id = os.path.splitext(os.path.basename(file_path))[0].split('_')[0]
    source = source_hint or "UNKNOWN"
    session_inserted = False
    name = None
    record_num = 0

    allowed_names = ["hrv", "f3b monitor+hrv", "meditation"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for msg in fit_file.messages:

        if msg.name == 'sport':
            fields = {field.name: field.value for field in msg.fields}
            name = fields.get('name')  # e.g., "HRV", "Cycling", etc.
            if name:
                name = name.strip()
            # Skip everything if sport name not in allowed list
            if not name or name.lower() not in allowed_names:
                logging.info(f"Skipping file {file_path} because name '{name}' not in {allowed_names}")
                break

        if msg.name == 'record' and name and name.lower() in allowed_names:
            fields = {field.name: field.value for field in msg.fields}
            cursor.execute('''
                INSERT OR IGNORE INTO hrv_records (
                    activity_id, name, record, source, timestamp, hrv_s, hrv_btb, hrv_hr, rrhr,
                    rawHR, RRint, hrv, rmssd, sdnn, SaO2_C, stress_hrp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity_id,
                name,
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

        elif msg.name == 'session' and not session_inserted and name and name.lower() in allowed_names:
            fields = {field.name: field.value for field in msg.fields}
            cursor.execute('''
                INSERT OR IGNORE INTO hrv_sessions (
                    activity_id, name, source, timestamp, sport, min_hr, hrv_rmssd, hrv_sdrr_f,
                    hrv_sdrr_l, hrv_pnn50, hrv_pnn20, armssd, asdnn, SaO2, trnd_hrv, recovery,
                    sdnn, sdsd, dBeats, sBeats, session_hrv, NN50, NN20, sd1, sd2, lf, hf, vlf,
                    pNN50, lf_nu, hf_nu, mean_hr, mean_rr, stress_hrpa, steps, distance, vo2max
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity_id,
                name,
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
    SELECT date(timestamp) as date, AVG(hrv_armssd) as avg_rmssd, AVG(sdnn) as avg_sdnn
    FROM hrv_sessions
    WHERE timestamp >= date('now', ?) and name is 'F3b Monitor+HRV'
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

def calculate_recovery_score(activity_id, conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT armssd, asdnn, nn50 FROM hrv_sessions WHERE name is 'F3b Monitor+HRV' AND activity_id = ?
    """, (activity_id,))
    result = cursor.fetchone()
    if result and all(result):
        rmssd_score = min(100, result[0] / 2)
        sdnn_score = min(100, result[1] / 2)
        pnn50_score = result[2] or 0
        recovery_score = (rmssd_score + sdnn_score + pnn50_score) / 3
        return recovery_score
    else:
        return None

def calculate_all_recovery_scores():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT activity_id FROM hrv_sessions")
    activity_ids = [row[0] for row in cursor.fetchall()]
    results = []
    for activity_id in activity_ids:
        score = calculate_recovery_score(activity_id, conn)
        results.append((activity_id, score))
        print(f"Recovery score for {activity_id}: {score if score is not None else 'No data'}")
    conn.close()
    return results



# --- Enhanced HRV Pattern Detection ---
def establish_baseline(days=21):
    """Establish personal HRV baseline over specified days"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT date(timestamp) as date, AVG(hrv_rmssd) as avg_rmssd, 
           AVG(sdnn) as avg_sdnn, AVG(hrv_pnn50) as avg_pnn50
    FROM hrv_sessions
    WHERE timestamp >= date('now', ?) AND hrv_rmssd IS NOT NULL
    GROUP BY date(timestamp)
    ORDER BY date(timestamp) DESC
    """
    df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
    conn.close()
    
    if len(df) < 14:
        print(f"Warning: Only {len(df)} days of data available. Need at least 14 days for reliable baseline.")
        return None
    
    baseline = {
        'rmssd_mean': df['avg_rmssd'].mean(),
        'rmssd_std': df['avg_rmssd'].std(),
        'rmssd_lower': df['avg_rmssd'].quantile(0.25),
        'rmssd_upper': df['avg_rmssd'].quantile(0.75),
        'sdnn_mean': df['avg_sdnn'].mean(),
        'sdnn_std': df['avg_sdnn'].std(),
        'days_calculated': len(df)
    }
    
    print(f"Baseline established over {baseline['days_calculated']} days:")
    print(f"RMSSD: {baseline['rmssd_mean']:.1f} ± {baseline['rmssd_std']:.1f}")
    print(f"Normal range: {baseline['rmssd_lower']:.1f} - {baseline['rmssd_upper']:.1f}")
    
    return baseline

def detect_hrv_drops(baseline, days=7, drop_threshold=0.7):
    """Detect sudden HRV drops below baseline"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT date(timestamp) as date, AVG(hrv_rmssd) as avg_rmssd,
           AVG(sdnn) as avg_sdnn, COUNT(*) as readings
    FROM hrv_sessions
    WHERE timestamp >= date('now', ?) AND hrv_rmssd IS NOT NULL
    GROUP BY date(timestamp)
    ORDER BY date(timestamp) DESC
    """
    df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
    conn.close()
    
    if baseline is None or df.empty:
        print("No baseline or recent data available for drop detection.")
        return []
    
    alerts = []
    threshold = baseline['rmssd_lower'] * drop_threshold
    
    for _, row in df.iterrows():
        if row['avg_rmssd'] < threshold:
            severity = "SEVERE" if row['avg_rmssd'] < (baseline['rmssd_mean'] * 0.6) else "MODERATE"
            alerts.append({
                'date': row['date'],
                'rmssd': row['avg_rmssd'],
                'severity': severity,
                'drop_percent': ((baseline['rmssd_mean'] - row['avg_rmssd']) / baseline['rmssd_mean']) * 100
            })
    
    return alerts

def detect_sustained_low_hrv(baseline, days=14, consecutive_days=3):
    """Detect sustained low HRV periods"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT date(timestamp) as date, AVG(hrv_rmssd) as avg_rmssd
    FROM hrv_sessions
    WHERE timestamp >= date('now', ?) AND hrv_rmssd IS NOT NULL
    GROUP BY date(timestamp)
    ORDER BY date(timestamp) ASC
    """
    df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
    conn.close()
    
    if baseline is None or len(df) < consecutive_days:
        return []
    
    threshold = baseline['rmssd_lower']
    sustained_periods = []
    current_period = []
    
    for _, row in df.iterrows():
        if row['avg_rmssd'] < threshold:
            current_period.append(row)
        else:
            if len(current_period) >= consecutive_days:
                sustained_periods.append({
                    'start_date': current_period[0]['date'],
                    'end_date': current_period[-1]['date'],
                    'duration_days': len(current_period),
                    'avg_rmssd': np.mean([r['avg_rmssd'] for r in current_period])
                })
            current_period = []
    
    # Check if current period is still ongoing
    if len(current_period) >= consecutive_days:
        sustained_periods.append({
            'start_date': current_period[0]['date'],
            'end_date': current_period[-1]['date'],
            'duration_days': len(current_period),
            'avg_rmssd': np.mean([r['avg_rmssd'] for r in current_period]),
            'ongoing': True
        })
    
    return sustained_periods

def calculate_hrv_7day_average():
    """Calculate rolling 7-day HRV average"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT date(timestamp) as date, AVG(hrv_rmssd) as daily_rmssd
    FROM hrv_sessions
    WHERE timestamp >= date('now', '-30 days') AND hrv_rmssd IS NOT NULL
    GROUP BY date(timestamp)
    ORDER BY date(timestamp) DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if len(df) < 7:
        print("Not enough data for 7-day average calculation.")
        return None
    
    df['rolling_7day'] = df['daily_rmssd'].rolling(window=7, min_periods=4).mean()
    df['trend_direction'] = df['rolling_7day'].diff()
    
    return df

def detect_erratic_patterns(days=14):
    """Detect erratic HRV patterns (high variability)"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT date(timestamp) as date, AVG(hrv_rmssd) as avg_rmssd,
           STDEV(hrv_rmssd) as std_rmssd, COUNT(*) as readings
    FROM hrv_sessions
    WHERE timestamp >= date('now', ?) AND hrv_rmssd IS NOT NULL
    GROUP BY date(timestamp)
    HAVING COUNT(*) > 1
    ORDER BY date(timestamp) DESC
    """
    df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
    conn.close()
    
    if df.empty:
        return []
    
    # Calculate coefficient of variation for each day
    df['cv'] = df['std_rmssd'] / df['avg_rmssd']
    high_variability_threshold = df['cv'].quantile(0.8)  # Top 20% most variable days
    
    erratic_days = df[df['cv'] > high_variability_threshold].copy()
    
    return erratic_days[['date', 'avg_rmssd', 'std_rmssd', 'cv']].to_dict('records')

def comprehensive_hrv_health_check():
    """Run comprehensive HRV health monitoring"""
    print("=== HRV Health Monitoring Report ===")
    print(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Establish baseline
    baseline = establish_baseline(days=21)
    print()
    
    # Check for recent drops
    print("--- Recent HRV Drops ---")
    drops = detect_hrv_drops(baseline, days=7)
    if drops:
        for drop in drops:
            print(f"⚠️  {drop['date']}: RMSSD {drop['rmssd']:.1f} ({drop['severity']} - {drop['drop_percent']:.1f}% below baseline)")
    else:
        print("✅ No significant HRV drops detected in the last 7 days.")
    print()
    
    # Check for sustained low periods
    print("--- Sustained Low HRV Periods ---")
    sustained = detect_sustained_low_hrv(baseline, days=14)
    if sustained:
        for period in sustained:
            ongoing = " (ONGOING)" if period.get('ongoing') else ""
            print(f"🔴 {period['start_date']} to {period['end_date']}: {period['duration_days']} days{ongoing}")
    else:
        print("✅ No sustained low HRV periods detected.")
    print()
    
    # Check for erratic patterns
    print("--- Erratic HRV Patterns ---")
    erratic = detect_erratic_patterns(days=14)
    if erratic:
        for day in erratic:
            print(f"📊 {day['date']}: High variability (CV: {day['cv']:.2f})")
    else:
        print("✅ No erratic HRV patterns detected.")
    print()
    
    # 7-day trend
    print("--- 7-Day HRV Trend ---")
    trend_df = calculate_hrv_7day_average()
    if trend_df is not None and len(trend_df) >= 7:
        latest_avg = trend_df.iloc[0]['rolling_7day']
        trend_direction = trend_df.iloc[0]['trend_direction']
        if baseline:
            vs_baseline = ((latest_avg - baseline['rmssd_mean']) / baseline['rmssd_mean']) * 100
            print(f"Current 7-day average: {latest_avg:.1f} ({vs_baseline:+.1f}% vs baseline)")
        else:
            print(f"Current 7-day average: {latest_avg:.1f}")
        
        if trend_direction > 0:
            print("📈 Trend: Improving")
        elif trend_direction < 0:
            print("📉 Trend: Declining")
        else:
            print("➡️ Trend: Stable")
    else:
        print("Insufficient data for trend analysis.")
    print()
    
    # Health status summary
    print("--- Health Status Summary ---")
    risk_factors = 0
    if drops:
        risk_factors += len(drops)
    if sustained:
        risk_factors += len(sustained) * 2  # Weight sustained periods more heavily
    if erratic:
        risk_factors += len(erratic)
    
    if risk_factors == 0:
        print("✅ LOW RISK: HRV patterns appear normal")
    elif risk_factors <= 2:
        print("⚠️  MODERATE RISK: Some concerning patterns detected")
    else:
        print("🔴 HIGH RISK: Multiple concerning patterns detected")
    
    print(f"Risk factors detected: {risk_factors}")
    print("=== End Report ===")

# --- Main Execution ---
if __name__ == "__main__":
    create_unified_tables()
    # Example: ingest all .fit files from a folder
    # ingest_folder("C:/smakryko/myHealthData/HealtDataSystemAnalysis/TestFitFiles/Garmin", source_hint="GARMIN")
    
    ingest_folder("c:/users/jheel/jheelhealthdata/fitfiles/activities", source_hint="GARMIN")
    
    # ingest_folder("C:/smakryko/myHealthData/FitFiles/Activities", source_hint="GARMIN")
    # Run analytics
    analyze_hrv_trends(days=30)
    calculate_all_recovery_scores()
    # Example recovery score
    # calculate_recovery_score("your_activity_id_here")
    # Run comprehensive health check
    comprehensive_hrv_health_check()
